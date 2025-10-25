"""
Ассемблер для двухадресного RISC процессора
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from .models import AddressingMode

class RISCAssembler:
    """Ассемблер для двухадресного RISC процессора"""
    
    def __init__(self):
        self.instructions = {
            # Арифметико-логические команды
            'ADD': 0x01,    # ADD rd, rs1, rs2
            'SUB': 0x02,    # SUB rd, rs1, rs2
            'MUL': 0x03,    # MUL rd, rs1, rs2
            'DIV': 0x04,    # DIV rd, rs1, rs2
            'AND': 0x05,    # AND rd, rs1, rs2
            'OR':  0x06,    # OR  rd, rs1, rs2
            'XOR': 0x07,    # XOR rd, rs1, rs2
            'NOT': 0x08,    # NOT rd, rs1
            
            # Команды пересылки данных
            'MOV': 0x10,    # MOV rd, rs1
            'LDI': 0x11,    # LDI rd, imm
            'LDR': 0x12,    # LDR rd, [address]
            'LDRR': 0x13,   # LDRR rd, [rs1]
            'STR': 0x14,    # STR rs1, [address]
            'STRR': 0x15,   # STRR rs1, [rd]
            
            # Команды сравнения и переходов
            'CMP': 0x20,    # CMP rs1, rs2
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
    
    def _parse_register(self, reg_str: str) -> int:
        """Парсинг регистра (R0-R7)"""
        reg_str = reg_str.upper().strip()
        if reg_str.startswith('R') and len(reg_str) == 2:
            reg_num = int(reg_str[1])
            if 0 <= reg_num <= 7:
                return reg_num
        raise ValueError(f"Invalid register: {reg_str}")
    
    def _parse_operand(self, operand_str: str) -> Tuple[Any, AddressingMode]:
        """Парсинг операнда с определением типа адресации"""
        operand_str = operand_str.strip()
        
        # Непосредственная адресация (число)
        if operand_str.isdigit() or (operand_str.startswith('-') and operand_str[1:].isdigit()):
            return self._parse_number(operand_str), AddressingMode.IMMEDIATE
        
        # Шестнадцатеричное число
        if operand_str.startswith('0x'):
            return self._parse_number(operand_str), AddressingMode.IMMEDIATE
        
        # Регистровая адресация (R0-R7)
        if operand_str.upper().startswith('R') and len(operand_str) == 2:
            return self._parse_register(operand_str), AddressingMode.REGISTER
        
        # Прямая адресация [address]
        if operand_str.startswith('[') and operand_str.endswith(']'):
            address_str = operand_str[1:-1].strip()
            # Проверяем, является ли содержимое регистром
            if address_str.upper().startswith('R') and len(address_str) == 2:
                return self._parse_register(address_str), AddressingMode.INDIRECT_REGISTER
            else:
                return self._parse_number(address_str), AddressingMode.DIRECT
        
        # Метка (для переходов)
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
        parts = line.split()
        if not parts:
            return label, None, None
        
        instruction = parts[0].upper()
        operands = parts[1:] if len(parts) > 1 else []
        
        return label, instruction, operands
    
    def _encode_instruction(self, opcode: int, rd: int = 0, rs1: int = 0, rs2: int = 0, 
                          immediate: int = 0, addressing_mode: AddressingMode = AddressingMode.REGISTER) -> int:
        """Кодирование инструкции в машинный код"""
        # Формат команды: 16 бит для простых команд, 32 бита для сложных
        # [15:12] - код операции (4 бита)
        # [11:9]  - регистр назначения rd (3 бита)
        # [8:6]   - первый исходный регистр rs1 (3 бита)
        # [5:3]   - второй исходный регистр rs2 (3 бита)
        # [2:0]   - режим адресации (3 бита)
        
        # Для команд с непосредственными значениями используем 32-битный формат
        if addressing_mode == AddressingMode.IMMEDIATE and immediate != 0:
            # 32-битный формат: [31:16] - immediate, [15:0] - остальные поля
            return (immediate << 16) | (opcode << 12) | (rd << 9) | (rs1 << 6) | (rs2 << 3) | self._addressing_mode_to_code(addressing_mode)
        else:
            # 16-битный формат
            return (opcode << 12) | (rd << 9) | (rs1 << 6) | (rs2 << 3) | self._addressing_mode_to_code(addressing_mode)
    
    def _addressing_mode_to_code(self, mode: AddressingMode) -> int:
        """Преобразование режима адресации в код"""
        mode_codes = {
            AddressingMode.IMMEDIATE: 0,
            AddressingMode.DIRECT: 1,
            AddressingMode.REGISTER: 2,
            AddressingMode.INDIRECT_REGISTER: 3
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
        
        # Первый проход: сбор меток
        for i, line in enumerate(lines):
            label, instruction, operands = self.parse_line(line, resolve_labels=False)
            if label:
                labels[label] = i
            if instruction:
                machine_code.append(self._format_instruction(instruction, operands or []))
        
        # Второй проход: замена меток на адреса
        resolved_code = []
        for i, instruction_line in enumerate(machine_code):
            parts = instruction_line.split()
            if len(parts) >= 2:
                instruction = parts[0]
                operands = parts[1:]
                
                # Заменяем метки на адреса
                resolved_operands = []
                for operand in operands:
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
        
        # Определяем тип команды и операнды
        if instruction in ['ADD', 'SUB', 'MUL', 'DIV', 'AND', 'OR', 'XOR']:
            return {
                "opcode": opcode,
                "type": "R",
                "description": f"{instruction} rd, rs1, rs2",
                "operands": ["rd", "rs1", "rs2"],
                "addressing_modes": ["register"]
            }
        elif instruction in ['NOT', 'MOV', 'LDRR', 'STRR']:
            return {
                "opcode": opcode,
                "type": "R",
                "description": f"{instruction} rd, rs1",
                "operands": ["rd", "rs1"],
                "addressing_modes": ["register"]
            }
        elif instruction in ['LDI']:
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} rd, immediate",
                "operands": ["rd", "immediate"],
                "addressing_modes": ["immediate"]
            }
        elif instruction in ['LDR', 'STR']:
            return {
                "opcode": opcode,
                "type": "I",
                "description": f"{instruction} rd, [address]",
                "operands": ["rd", "address"],
                "addressing_modes": ["direct"]
            }
        elif instruction in ['CMP']:
            return {
                "opcode": opcode,
                "type": "R",
                "description": f"{instruction} rs1, rs2",
                "operands": ["rs1", "rs2"],
                "addressing_modes": ["register"]
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