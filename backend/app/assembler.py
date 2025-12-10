"""
Ассемблер для одноадресного процессора Фон-Неймана
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from .models import AddressingMode

class RISCAssembler:
    """Ассемблер для одноадресного процессора Фон-Неймана"""
    
    def __init__(self):
        self.instructions = {
            # Арифметико-логические команды
            'ADD': 0x01,    # ADD operand - ACC = ACC + operand
            'SUB': 0x02,    # SUB operand - ACC = ACC - operand
            'MUL': 0x03,    # MUL operand - ACC = ACC * operand
            'DIV': 0x04,    # DIV operand - ACC = ACC / operand
            'AND': 0x05,    # AND operand - ACC = ACC & operand
            'OR':  0x06,    # OR  operand - ACC = ACC | operand
            'XOR': 0x07,    # XOR operand - ACC = ACC ^ operand
            'NOT': 0x08,    # NOT - ACC = ~ACC
            
            # Команды пересылки данных
            'LDA': 0x10,    # LDA operand - ACC = operand
            'STA': 0x11,    # STA operand - [operand] = ACC
            'LDI': 0x12,    # LDI imm - ACC = immediate
            
            # Команды сравнения и переходов
            'CMP': 0x20,    # CMP operand - сравнить ACC и operand
            'JMP': 0x21,    # JMP address
            'JZ':  0x22,    # JZ address
            'JNZ': 0x23,    # JNZ address
            'JC':  0x24,    # JC address
            'JNC': 0x25,    # JNC address
            'JV':  0x26,    # JV address
            'JNV': 0x27,    # JNV address
            'JN':  0x28,    # JN address
            'JNN': 0x29,    # JNN address
            
            # Системные команды
            'HALT': 0xFF,   # HALT
            'NOP':  0x00,   # NOP
        }
    
    def _parse_number(self, value: str) -> int:
        """Парсинг числовых значений в разных форматах"""
        value = value.strip().lower()
        
        if value.startswith('0x'):
            return int(value[2:], 16)
        elif value.startswith('0b'):
            return int(value[2:], 2)
        else:
            return int(value)
    
    def _parse_operand(self, operand_str: str) -> Tuple[Any, AddressingMode]:
        """Парсинг операнда с определением типа адресации (одноадресная архитектура)
        
        Форматы:
        - Непосредственное значение: LDA 100 (десятичное число без префикса)
        - Прямой адрес: LDA [0x0100] или LDA 0x0100 (hex с префиксом 0x)
        """
        operand_str = operand_str.strip()
        
        # Прямая адресация [address] - всегда прямой адрес памяти
        if operand_str.startswith('[') and operand_str.endswith(']'):
            address_str = operand_str[1:-1].strip()
            return self._parse_number(address_str), AddressingMode.DIRECT
        
        # Шестнадцатеричное число (0x...) - прямой адрес памяти
        if operand_str.startswith('0x') or operand_str.startswith('0X'):
            addr = self._parse_number(operand_str)
            return addr, AddressingMode.DIRECT
        
        # Десятичное число (без префикса) - непосредственное значение
        if operand_str.isdigit() or (operand_str.startswith('-') and operand_str[1:].isdigit()):
            val = self._parse_number(operand_str)
            return val, AddressingMode.IMMEDIATE
        
        # Метка (для переходов) - будет разрешена позже
        return operand_str, AddressingMode.IMMEDIATE
    
    def parse_line(self, line: str, resolve_labels: bool = False, labels: Dict[str, int] = None) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
        """Парсинг строки ассемблера"""
        line = line.strip()
        
        # Пропускаем пустые строки и комментарии
        if not line or line.startswith(';'):
            return None, None, None
        
        # Удаляем комментарии
        if ';' in line:
            line = line[:line.index(';')].strip()
        
        # Парсим метки
        label = None
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip()
            line = parts[1].strip()
        
        # Парсим инструкцию и операнды
        # Разделяем команду и операнды, учитывая запятые
        parts = line.replace(',', ' ').split()
        if not parts:
            return label, None, None
        
        instruction = parts[0].upper()
        operands = [p.strip() for p in parts[1:] if p.strip()] if len(parts) > 1 else []
        
        return label, instruction, operands
    
    def _encode_instruction(self, opcode: int, operand: int = 0, 
                          addressing_mode: AddressingMode = AddressingMode.IMMEDIATE) -> int:
        """Кодирование инструкции в машинный код (одноадресная архитектура)
        
        Формат команды:
        - 16 бит: [15:12] - код операции (4 бита), [11:0] - адрес/значение (12 бит)
        - 32 бит (для непосредственных значений): [31:16] - значение (16 бит), [15:0] - код операции и адрес
        """
        # Для команд без операнда (NOT, HALT, NOP) используем 16-битный формат
        if operand == 0 and addressing_mode == AddressingMode.IMMEDIATE:
            # 16-битный формат: [15:12] - opcode, [11:0] - 0
            return (opcode << 12)
        
        # Для команд с непосредственными значениями (IMMEDIATE режим)
        if addressing_mode == AddressingMode.IMMEDIATE and operand != 0:
            # Если значение помещается в 12 бит, используем 16-битный формат
            if operand <= 0xFFF:
                # 16-битный формат: [15:12] - opcode, [11:0] - immediate value
                return (opcode << 12) | (operand & 0xFFF)
            else:
                # Если значение не помещается в 12 бит, используем 32-битный формат
                # 32-битный формат: [31:16] - immediate value (16 бит), [15:12] - opcode, [11:0] - 0
                return (operand << 16) | (opcode << 12)
        
        # Для команд с адресами памяти (DIRECT режим) используем 16-битный формат
        if addressing_mode == AddressingMode.DIRECT:
            # 16-битный формат: [15:12] - opcode, [11:0] - address (12 бит, максимум 0xFFF)
            if operand > 0xFFF:
                raise Exception(f"Address {operand} exceeds 12-bit limit (0xFFF)")
            return (opcode << 12) | (operand & 0xFFF)
        
        # По умолчанию 16-битный формат
        return (opcode << 12) | (operand & 0xFFF)
    
    def _addressing_mode_to_code(self, mode: AddressingMode) -> int:
        """Преобразование режима адресации в код (одноадресная архитектура)"""
        mode_codes = {
            AddressingMode.IMMEDIATE: 0,
            AddressingMode.DIRECT: 1
        }
        return mode_codes.get(mode, 0)
    
    def _format_instruction(self, instruction: str, operands: List[str], labels: Dict[str, int] = None) -> str:
        """Форматирование инструкции для отображения"""
        if not operands:
            return instruction
        
        formatted_operands = []
        for operand in operands:
            # Проверяем, является ли операнд меткой
            if labels and operand in labels:
                formatted_operands.append(str(labels[operand]))
            else:
                formatted_operands.append(operand)
        
        return f"{instruction} {', '.join(formatted_operands)}"
    
    def assemble(self, source_code: str) -> Tuple[List[str], Dict[str, int]]:
        """Ассемблирование исходного кода"""
        lines = source_code.split('\n')
        machine_code = []
        labels = {}
        
        # Первый проход: сбор меток и компиляция команд
        code_index = 0  # Индекс в скомпилированном коде
        for line in lines:
            label, instruction, operands = self.parse_line(line, resolve_labels=False)
            if label:
                # Метка указывает на индекс следующей команды в скомпилированном коде
                # Если на этой же строке есть команда, метка указывает на неё
                labels[label] = code_index
            if instruction:
                machine_code.append(self._format_instruction(instruction, operands or []))
                code_index += 1
        
        # Второй проход: замена меток на адреса
        resolved_code = []
        for i, instruction_line in enumerate(machine_code):
            # Парсим команду с учетом запятых
            parts = instruction_line.replace(',', ' ').split()
            if len(parts) >= 2:
                instruction = parts[0]
                operands_parts = parts[1:]
                
                # Заменяем метки на адреса
                resolved_operands = []
                for operand in operands_parts:
                    if operand in labels:
                        resolved_operands.append(str(labels[operand]))
                    else:
                        resolved_operands.append(operand)
                
                resolved_code.append(f"{instruction} {', '.join(resolved_operands)}")
            else:
                resolved_code.append(instruction_line)
        
        return resolved_code, labels
    
    def disassemble(self, machine_code: List[str]) -> str:
        """Дизассемблирование машинного кода"""
        result = []
        for i, instruction in enumerate(machine_code):
            result.append(f"{i:04X}: {instruction}")
        return '\n'.join(result)
    
    def get_instruction_info(self, instruction: str) -> Dict[str, Any]:
        """Получить информацию об инструкции"""
        instruction = instruction.upper().strip()
        
        if instruction not in self.instructions:
            return {"error": f"Unknown instruction: {instruction}"}
        
        opcode = self.instructions[instruction]
        
        # Определяем тип команды и операнды (одноадресная архитектура)
        if instruction in ['ADD', 'SUB', 'MUL', 'DIV', 'AND', 'OR', 'XOR']:
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} operand",
                "operands": ["operand"],
                "addressing_modes": ["immediate", "direct"]
            }
        elif instruction == 'NOT':
            return {
                "opcode": opcode,
                "type": "S",
                "description": f"{instruction}",
                "operands": [],
                "addressing_modes": []
            }
        elif instruction in ['LDA', 'STA']:
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} operand",
                "operands": ["operand"],
                "addressing_modes": ["immediate", "direct"]
            }
        elif instruction == 'LDI':
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} immediate",
                "operands": ["immediate"],
                "addressing_modes": ["immediate"]
            }
        elif instruction == 'CMP':
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} operand",
                "operands": ["operand"],
                "addressing_modes": ["immediate", "direct"]
            }
        elif instruction in ['JMP', 'JZ', 'JNZ', 'JC', 'JNC', 'JV', 'JNV', 'JN', 'JNN']:
            return {
                "opcode": opcode,
                "type": "J",
                "description": f"{instruction} address",
                "operands": ["address"],
                "addressing_modes": ["immediate", "direct"]
            }
        elif instruction in ['HALT', 'NOP']:
            return {
                "opcode": opcode,
                "type": "S",
                "description": instruction,
                "operands": [],
                "addressing_modes": []
            }
        
        return {"error": f"Unknown instruction: {instruction}"}