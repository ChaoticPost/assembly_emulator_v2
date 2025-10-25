"""
Эмулятор двухадресного RISC процессора с архитектурой Фон-Неймана
"""
from typing import List, Dict, Any, Optional, Tuple
from .models import ProcessorState, MemoryState, AddressingMode, InstructionField

class RISCProcessor:
    """Эмулятор двухадресного RISC процессора"""
    
    def __init__(self, memory_size: int = 4096):
        self.memory_size = memory_size
        self.processor = ProcessorState()
        self.memory = MemoryState()
        self.memory.ram = [0] * memory_size
        self.labels = {}  # Метки для переходов
        self.compiled_code = []
        self.source_code = ""
        
        # Система команд RISC процессора
        self.instructions = {
            # Арифметико-логические команды (R-тип)
            'ADD': 0x01,    # ADD rd, rs1, rs2 - rd = rs1 + rs2
            'SUB': 0x02,    # SUB rd, rs1, rs2 - rd = rs1 - rs2
            'MUL': 0x03,    # MUL rd, rs1, rs2 - rd = rs1 * rs2
            'DIV': 0x04,    # DIV rd, rs1, rs2 - rd = rs1 / rs2
            'AND': 0x05,    # AND rd, rs1, rs2 - rd = rs1 & rs2
            'OR':  0x06,    # OR  rd, rs1, rs2 - rd = rs1 | rs2
            'XOR': 0x07,    # XOR rd, rs1, rs2 - rd = rs1 ^ rs2
            'NOT': 0x08,    # NOT rd, rs1     - rd = ~rs1
            
            # Команды пересылки данных (I-тип)
            'MOV': 0x10,    # MOV rd, rs1     - rd = rs1
            'LDI': 0x11,    # LDI rd, imm     - rd = immediate
            'LDR': 0x12,    # LDR rd, [rs1]   - rd = [rs1] (прямая адресация)
            'LDRR': 0x13,   # LDRR rd, [rs1]  - rd = [rs1] (косвенно-регистровая)
            'STR': 0x14,    # STR rs1, [rd]   - [rd] = rs1 (прямая адресация)
            'STRR': 0x15,   # STRR rs1, [rd]  - [rd] = rs1 (косвенно-регистровая)
            
            # Команды сравнения и переходов (I-тип)
            'CMP': 0x20,    # CMP rs1, rs2    - сравнить rs1 и rs2
            'JMP': 0x21,    # JMP addr        - безусловный переход
            'JZ':  0x22,    # JZ addr         - переход если Z=1
            'JNZ': 0x23,    # JNZ addr        - переход если Z=0
            'JC':  0x24,    # JC addr         - переход если C=1
            'JNC': 0x25,    # JNC addr        - переход если C=0
            'JV':  0x26,    # JV addr         - переход если V=1
            'JNV': 0x27,    # JNV addr        - переход если V=0
            'JN':  0x28,    # JN addr         - переход если N=1
            'JNN': 0x29,    # JNN addr        - переход если N=0
            
            # Системные команды
            'HALT': 0xFF,   # HALT            - остановка
            'NOP':  0x00,   # NOP             - нет операции
        }
    
    def reset(self):
        """Сброс процессора в начальное состояние"""
        self.processor = ProcessorState()
        self.memory = MemoryState()
        self.memory.ram = [0] * self.memory_size
        self.labels = {}
        self.compiled_code = []
        self.source_code = ""
    
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
            address_str = operand_str[1:-1]
            return self._parse_number(address_str), AddressingMode.DIRECT
        
        # Косвенно-регистровая адресация [R0-R7]
        if operand_str.startswith('[') and operand_str.endswith(']'):
            inner = operand_str[1:-1].strip()
            if inner.upper().startswith('R') and len(inner) == 2:
                return self._parse_register(inner), AddressingMode.INDIRECT_REGISTER
        
        # Метка (для переходов)
        return operand_str, AddressingMode.IMMEDIATE
    
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
    
    def _decode_instruction(self, instruction: int) -> InstructionField:
        """Декодирование инструкции для отображения полей"""
        if instruction > 0xFFFF:  # 32-битная команда
            immediate = instruction >> 16
            opcode = (instruction >> 12) & 0xF
            rd = (instruction >> 9) & 0x7
            rs1 = (instruction >> 6) & 0x7
            rs2 = (instruction >> 3) & 0x7
            addr_mode_code = instruction & 0x7
        else:  # 16-битная команда
            immediate = 0
            opcode = (instruction >> 12) & 0xF
            rd = (instruction >> 9) & 0x7
            rs1 = (instruction >> 6) & 0x7
            rs2 = (instruction >> 3) & 0x7
            addr_mode_code = instruction & 0x7
        
        # Определяем режим адресации
        mode_codes = {0: AddressingMode.IMMEDIATE, 1: AddressingMode.DIRECT, 
                     2: AddressingMode.REGISTER, 3: AddressingMode.INDIRECT_REGISTER}
        addressing_mode = mode_codes.get(addr_mode_code, AddressingMode.REGISTER)
        
        # Определяем тип команды
        instruction_type = "I" if immediate != 0 else "R"
        
        return InstructionField(
            opcode=opcode,
            opcode_bits=format(opcode, '04b'),
            rd=rd,
            rd_bits=format(rd, '03b'),
            rs1=rs1,
            rs1_bits=format(rs1, '03b'),
            rs2=rs2,
            rs2_bits=format(rs2, '03b'),
            immediate=immediate,
            immediate_bits=format(immediate, '016b') if immediate != 0 else "",
            addressing_mode=addressing_mode,
            instruction_type=instruction_type
        )
    
    def _get_operand_value(self, operand: Any, addressing_mode: AddressingMode) -> int:
        """Получение значения операнда в зависимости от режима адресации"""
        if addressing_mode == AddressingMode.IMMEDIATE:
            return operand
        elif addressing_mode == AddressingMode.REGISTER:
            return self.processor.registers[operand]
        elif addressing_mode == AddressingMode.DIRECT:
            if 0 <= operand < self.memory_size:
                return self.memory.ram[operand]
            return 0
        elif addressing_mode == AddressingMode.INDIRECT_REGISTER:
            addr = self.processor.registers[operand]
            if 0 <= addr < self.memory_size:
                return self.memory.ram[addr]
            return 0
        return 0
    
    def _set_operand_value(self, operand: Any, value: int, addressing_mode: AddressingMode):
        """Установка значения операнда в зависимости от режима адресации"""
        if addressing_mode == AddressingMode.REGISTER:
            self.processor.registers[operand] = value
        elif addressing_mode == AddressingMode.DIRECT:
            if 0 <= operand < self.memory_size:
                self.memory.ram[operand] = value
        elif addressing_mode == AddressingMode.INDIRECT_REGISTER:
            addr = self.processor.registers[operand]
            if 0 <= addr < self.memory_size:
                self.memory.ram[addr] = value
    
    def update_flags(self, result: int, operation: str = ""):
        """Обновление флагов после операции"""
        self.processor.flags["zero"] = (result == 0)
        self.processor.flags["negative"] = (result < 0)
        
        # Проверка переполнения для 16-битных чисел
        if result > 32767 or result < -32768:
            self.processor.flags["overflow"] = True
        else:
            self.processor.flags["overflow"] = False
        
        # Упрощенная логика для флага переноса
        if operation == "add" and result < 0:
            self.processor.flags["carry"] = True
        elif operation == "sub" and result > 0:
            self.processor.flags["carry"] = True
        else:
            self.processor.flags["carry"] = False
    
    def execute_instruction(self, instruction: str, operands: List[str] = None):
        """Выполнение одной инструкции"""
        instruction = instruction.upper().strip()
        operands = operands or []
        
        if instruction not in self.instructions:
            raise Exception(f"Unknown instruction: {instruction}")
        
        opcode = self.instructions[instruction]
        
        # Парсинг операндов
        if len(operands) >= 1:
            op1, mode1 = self._parse_operand(operands[0])
        else:
            op1, mode1 = 0, AddressingMode.REGISTER
            
        if len(operands) >= 2:
            op2, mode2 = self._parse_operand(operands[1])
        else:
            op2, mode2 = 0, AddressingMode.REGISTER
        
        # Выполнение команды
        if instruction == "ADD":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 + val2
            self.update_flags(result, "add")
            self.processor.registers[0] = result  # R0 - аккумулятор
            
        elif instruction == "SUB":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 - val2
            self.update_flags(result, "sub")
            self.processor.registers[0] = result
            
        elif instruction == "MUL":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 * val2
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "DIV":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            if val2 == 0:
                raise Exception("Division by zero")
            result = val1 // val2
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "AND":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 & val2
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "OR":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 | val2
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "XOR":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 ^ val2
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "NOT":
            val1 = self._get_operand_value(op1, mode1)
            result = ~val1
            self.update_flags(result)
            self.processor.registers[0] = result
            
        elif instruction == "MOV":
            val1 = self._get_operand_value(op1, mode1)
            self.processor.registers[0] = val1  # Всегда в R0
            
        elif instruction == "LDI":
            self.processor.registers[0] = op1  # Непосредственное значение
            
        elif instruction == "LDR":
            val1 = self._get_operand_value(op1, mode1)
            self.processor.registers[0] = val1
            
        elif instruction == "LDRR":
            val1 = self._get_operand_value(op1, mode1)
            self.processor.registers[0] = val1
            
        elif instruction == "STR":
            val1 = self.processor.registers[0]  # Из R0
            self._set_operand_value(op1, val1, mode1)
            
        elif instruction == "STRR":
            val1 = self.processor.registers[0]  # Из R0
            self._set_operand_value(op1, val1, mode1)
            
        elif instruction == "CMP":
            val1 = self._get_operand_value(op1, mode1)
            val2 = self._get_operand_value(op2, mode2)
            result = val1 - val2
            self.update_flags(result)
            
        elif instruction == "JMP":
            if mode1 == AddressingMode.IMMEDIATE:
                self.processor.program_counter = op1
            else:
                self.processor.program_counter = self._get_operand_value(op1, mode1)
            return  # Не увеличиваем PC
            
        elif instruction == "JZ":
            if self.processor.flags["zero"]:
                if mode1 == AddressingMode.IMMEDIATE:
                    self.processor.program_counter = op1
                else:
                    self.processor.program_counter = self._get_operand_value(op1, mode1)
                return
                
        elif instruction == "JNZ":
            if not self.processor.flags["zero"]:
                if mode1 == AddressingMode.IMMEDIATE:
                    self.processor.program_counter = op1
                else:
                    self.processor.program_counter = self._get_operand_value(op1, mode1)
                return
                
        elif instruction == "JC":
            if self.processor.flags["carry"]:
                if mode1 == AddressingMode.IMMEDIATE:
                    self.processor.program_counter = op1
                else:
                    self.processor.program_counter = self._get_operand_value(op1, mode1)
                return
                
        elif instruction == "JNC":
            if not self.processor.flags["carry"]:
                if mode1 == AddressingMode.IMMEDIATE:
                    self.processor.program_counter = op1
                else:
                    self.processor.program_counter = self._get_operand_value(op1, mode1)
                return
                
        elif instruction == "HALT":
            self.processor.is_halted = True
            return
            
        elif instruction == "NOP":
            pass
        
        # Увеличиваем счетчик команд, если не было перехода
        self.processor.program_counter += 1
    
    def step(self) -> bool:
        """Выполнить один шаг программы"""
        if self.processor.is_halted:
            return False
        
        if not self.compiled_code or self.processor.program_counter >= len(self.compiled_code):
            self.processor.is_halted = True
            return False
        
        # Получаем текущую команду
        instruction_line = self.compiled_code[self.processor.program_counter]
        parts = instruction_line.split()
        instruction = parts[0]
        operands = parts[1:] if len(parts) > 1 else []
        
        # Сохраняем команду в регистр команд
        self.processor.current_command = instruction_line
        self.processor.instruction_register_asm = instruction_line
        
        # Выполняем инструкцию
        try:
            self.execute_instruction(instruction, operands)
            self.processor.cycles += 1
            
            # Сохраняем состояние в историю
            self.memory.history.append({
                'command': instruction_line,
                'registers': self.processor.registers.copy(),
                'programCounter': self.processor.program_counter,
                'flags': self.processor.flags.copy()
            })
            
            return not self.processor.is_halted
            
        except Exception as e:
            self.processor.is_halted = True
            self.processor.current_command = f"ERROR: {str(e)}"
            return False
    
    def load_program(self, compiled_code: List[str], source_code: str = ""):
        """Загрузить скомпилированную программу"""
        self.compiled_code = compiled_code
        self.source_code = source_code
        self.processor.program_counter = 0
        self.processor.is_halted = False
        self.processor.current_command = ""
        self.processor.instruction_register_asm = ""
        self.memory.history = []
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние процессора"""
        return {
            "processor": {
                "registers": self.processor.registers.copy(),
                "program_counter": self.processor.program_counter,
                "instruction_register": self.processor.instruction_register,
                "instruction_register_asm": self.processor.instruction_register_asm,
                "flags": self.processor.flags.copy(),
                "current_command": self.processor.current_command,
                "is_halted": self.processor.is_halted,
                "cycles": self.processor.cycles
            },
            "memory": {
                "ram": self.memory.ram.copy(),
                "history": self.memory.history.copy()
            },
            "source_code": self.source_code,
            "machine_code": self.compiled_code,
            "current_task": None
        }