"""
Эмулятор двухадресного RISC процессора с архитектурой Фон-Неймана
"""
from typing import List, Dict, Any, Optional, Tuple
from .models import ProcessorState, MemoryState, AddressingMode, InstructionField

class RISCProcessor:
    """Эмулятор двухадресного RISC процессора"""
    
    def __init__(self, memory_size: int = 8192):
        self.memory_size = memory_size
        self.processor = ProcessorState()
        self.memory = MemoryState()
        self.memory.ram = [0] * memory_size
        self.labels = {}  # Метки для переходов
        self.compiled_code = []
        self.source_code = ""
        
        # Промежуточные переменные для системы фаз выполнения
        self._current_instruction_line = None
        self._current_instruction = None
        self._current_operands = None
        
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
        
        # Сбрасываем промежуточные переменные для системы фаз выполнения
        self._current_instruction_line = None
        self._current_instruction = None
        self._current_operands = None
    
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
        
        # Прямая и косвенно-регистровая адресация [address] или [R0-R7]
        if operand_str.startswith('[') and operand_str.endswith(']'):
            inner = operand_str[1:-1].strip()
            # Косвенно-регистровая адресация [R0-R7]
            if inner.upper().startswith('R') and len(inner) == 2:
                return self._parse_register(inner), AddressingMode.INDIRECT_REGISTER
            # Прямая адресация [address]
            else:
                addr = self._parse_number(inner)
                print(f"DEBUG _parse_operand: operand_str='{operand_str}', inner='{inner}', addr=0x{addr:04X}, mode=DIRECT")
                return addr, AddressingMode.DIRECT
        
        # Регистровая адресация (R0-R7)
        if operand_str.upper().startswith('R') and len(operand_str) == 2:
            return self._parse_register(operand_str), AddressingMode.REGISTER
        
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
            # КРИТИЧНО: Проверяем, что регистры инициализированы
            if not self.processor.registers:
                print(f"ERROR _get_operand_value REGISTER: Регистры не инициализированы! operand=R{operand}")
                return 0
            if operand < 0 or operand >= len(self.processor.registers):
                print(f"ERROR _get_operand_value REGISTER: Неверный номер регистра! operand=R{operand}, registers_count={len(self.processor.registers)}")
                return 0
            value = self.processor.registers[operand]
            print(f"DEBUG _get_operand_value REGISTER: operand=R{operand}, value=0x{value:04X} (decimal {value})")
            return value
        elif addressing_mode == AddressingMode.DIRECT:
            if 0 <= operand < len(self.memory.ram):
                value = self.memory.ram[operand]
                print(f"DEBUG _get_operand_value DIRECT: operand=0x{operand:04X}, value=0x{value:04X}, memory[0x{operand:04X}]=0x{value:04X}")
                return value
            print(f"DEBUG _get_operand_value DIRECT: operand=0x{operand:04X} OUT_OF_BOUNDS (memory_size=0x{len(self.memory.ram):04X})")
            return 0
        elif addressing_mode == AddressingMode.INDIRECT_REGISTER:
            addr = self.processor.registers[operand]
            if not self.memory.ram:
                print(f"DEBUG _get_operand_value INDIRECT_REGISTER: Память не инициализирована! operand=R{operand}, addr=0x{addr:04X}")
                return 0
            if 0 <= addr < len(self.memory.ram):
                value = self.memory.ram[addr]
                print(f"DEBUG _get_operand_value INDIRECT_REGISTER: operand=R{operand}, R{operand}=0x{addr:04X}, memory[0x{addr:04X}]=0x{value:04X} (decimal {value})")
                return value
            print(f"DEBUG _get_operand_value INDIRECT_REGISTER: operand=R{operand}, addr=0x{addr:04X} OUT_OF_BOUNDS (memory_size=0x{len(self.memory.ram):04X})")
            return 0
        return 0
    
    def _set_operand_value(self, operand: Any, value: int, addressing_mode: AddressingMode):
        """Установка значения операнда в зависимости от режима адресации"""
        if addressing_mode == AddressingMode.REGISTER:
            self._update_register(operand, value)
        elif addressing_mode == AddressingMode.DIRECT:
            # КРИТИЧНО: Создаем новый список для Pydantic, чтобы изменения были видны
            if not self.memory.ram:
                # Если память не инициализирована, создаем новую
                min_size = max(operand + 1, self.memory_size)
                self.memory.ram = [0] * min_size
                print(f"DEBUG _set_operand_value: Инициализирована память размером {min_size}")
            
            # Гарантируем достаточный размер памяти
            if operand >= len(self.memory.ram):
                new_ram = list(self.memory.ram)
                new_ram.extend([0] * (operand + 1 - len(new_ram)))
                self.memory.ram = new_ram
                print(f"DEBUG _set_operand_value: Расширена память до {len(self.memory.ram)} для адреса 0x{operand:04X}")
            
            # Создаем новый список для Pydantic
            new_ram = list(self.memory.ram)
            new_ram[operand] = int(value) & 0xFFFF
            self.memory.ram = new_ram
            print(f"DEBUG _set_operand_value: Записано значение 0x{value:04X} (decimal {value}) по адресу 0x{operand:04X}, ram[0x{operand:04X}]={self.memory.ram[operand]}")
        elif addressing_mode == AddressingMode.INDIRECT_REGISTER:
            addr = self.processor.registers[operand]
            # КРИТИЧНО: Создаем новый список для Pydantic, чтобы изменения были видны
            if not self.memory.ram:
                # Если память не инициализирована, создаем новую
                min_size = max(addr + 1, self.memory_size)
                self.memory.ram = [0] * min_size
                print(f"DEBUG _set_operand_value: Инициализирована память размером {min_size} для косвенной адресации")
            
            # Гарантируем достаточный размер памяти
            if addr >= len(self.memory.ram):
                new_ram = list(self.memory.ram)
                new_ram.extend([0] * (addr + 1 - len(new_ram)))
                self.memory.ram = new_ram
                print(f"DEBUG _set_operand_value: Расширена память до {len(self.memory.ram)} для косвенного адреса 0x{addr:04X}")
            
            # Создаем новый список для Pydantic
            new_ram = list(self.memory.ram)
            new_ram[addr] = int(value) & 0xFFFF
            self.memory.ram = new_ram
            print(f"DEBUG _set_operand_value: Записано значение 0x{value:04X} (decimal {value}) по косвенному адресу 0x{addr:04X} (R{operand}=0x{self.processor.registers[operand]:04X}), ram[0x{addr:04X}]={self.memory.ram[addr]}")
    
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
    
    def _update_register(self, rd: int, value: int):
        """Обновить регистр rd значением value (создает новый список для Pydantic)"""
        # Инициализируем регистры, если их нет
        if not self.processor.registers:
            self.processor.registers = [0] * 8
        
        # Создаем полностью новый список регистров (Pydantic требует нового объекта)
        new_registers = [int(r) & 0xFFFF for r in self.processor.registers[:8]]
        
        # Гарантируем, что у нас есть ровно 8 регистров
        while len(new_registers) < 8:
            new_registers.append(0)
        new_registers = new_registers[:8]
        
        # Обновляем нужный регистр
        if 0 <= rd < 8:
            new_registers[rd] = int(value) & 0xFFFF
        else:
            raise ValueError(f"Invalid register index: {rd} (must be 0-7)")
        
        # Обновляем регистры в процессоре (создаем новый список для Pydantic)
        # Важно: создаем полностью новый список, чтобы Pydantic увидел изменение
        self.processor.registers = new_registers
    
    def execute_instruction(self, instruction: str, operands: List[str] = None):
        """Выполнение одной инструкции"""
        instruction = instruction.upper().strip()
        operands = operands or []
        
        if instruction not in self.instructions:
            raise Exception(f"Unknown instruction: {instruction}")
        
        # Выполнение команды
        # Формат: ADD rd, rs1, rs2 - rd = rs1 + rs2
        if instruction == "ADD":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 + val2
                # Ограничиваем результат 16-битным значением (0x0000 - 0xFFFF)
                result = int(result) & 0xFFFF
                self.update_flags(result, "add")
                self._update_register(rd, result)
                print(f"DEBUG ADD: rd={rd}, result={result}, registers[{rd}]={self.processor.registers[rd]}, all_registers={self.processor.registers}")
            else:
                raise Exception(f"ADD requires 3 operands: ADD rd, rs1, rs2")
        
        # Формат: SUB rd, rs1, rs2 - rd = rs1 - rs2
        elif instruction == "SUB":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 - val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result, "sub")
                self._update_register(rd, result)
            else:
                raise Exception(f"SUB requires 3 operands: SUB rd, rs1, rs2")
        
        # Формат: MUL rd, rs1, rs2 - rd = rs1 * rs2
        elif instruction == "MUL":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 * val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"MUL requires 3 operands: MUL rd, rs1, rs2")
        
        # Формат: DIV rd, rs1, rs2 - rd = rs1 / rs2
        elif instruction == "DIV":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                if val2 == 0:
                    raise Exception("Division by zero")
                result = val1 // val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"DIV requires 3 operands: DIV rd, rs1, rs2")
            
        # Формат: AND rd, rs1, rs2 - rd = rs1 & rs2
        elif instruction == "AND":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 & val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"AND requires 3 operands: AND rd, rs1, rs2")
            
        # Формат: OR rd, rs1, rs2 - rd = rs1 | rs2
        elif instruction == "OR":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 | val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"OR requires 3 operands: OR rd, rs1, rs2")
            
        # Формат: XOR rd, rs1, rs2 - rd = rs1 ^ rs2
        elif instruction == "XOR":
            if len(operands) >= 3:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                rs2, mode2 = self._parse_operand(operands[2])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 ^ val2
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"XOR requires 3 operands: XOR rd, rs1, rs2")
            
        # Формат: NOT rd, rs1 - rd = ~rs1
        elif instruction == "NOT":
            if len(operands) >= 2:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                val1 = self._get_operand_value(rs1, mode1)
                result = ~val1
                # Ограничиваем результат 16-битным значением
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_register(rd, result)
            else:
                raise Exception(f"NOT requires 2 operands: NOT rd, rs1")
            
        # Формат: MOV rd, rs1 - rd = rs1
        elif instruction == "MOV":
            if len(operands) >= 2:
                rd, _ = self._parse_operand(operands[0])
                rs1, mode1 = self._parse_operand(operands[1])
                val1 = self._get_operand_value(rs1, mode1)
                # Ограничиваем значение 16-битным диапазоном
                val1 = val1 & 0xFFFF
                self._update_register(rd, val1)
            else:
                raise Exception(f"MOV requires 2 operands: MOV rd, rs1")
            
        # Формат: LDI rd, imm - rd = immediate
        elif instruction == "LDI":
            if len(operands) >= 2:
                rd, _ = self._parse_operand(operands[0])
                imm, _ = self._parse_operand(operands[1])
                # Ограничиваем значение 16-битным диапазоном (0x0000 - 0xFFFF)
                imm = int(imm) & 0xFFFF
                self._update_register(rd, imm)
                print(f"DEBUG LDI: rd={rd}, imm={imm}, registers[{rd}]={self.processor.registers[rd]}, all_registers={self.processor.registers}")
            else:
                raise Exception(f"LDI requires 2 operands: LDI rd, imm")
            
        # Формат: LDR rd, [address] - rd = [address]
        elif instruction == "LDR":
            if len(operands) >= 2:
                rd, _ = self._parse_operand(operands[0])
                addr, mode1 = self._parse_operand(operands[1])
                
                # Проверяем, что режим адресации правильный
                if mode1 != AddressingMode.DIRECT:
                    raise Exception(f"LDR requires DIRECT addressing mode, got {mode1}")
                
                # Проверяем, что адрес в пределах памяти
                if addr < 0:
                    print(f"ERROR LDR: Negative address 0x{addr:04X}")
                    mem_val = 0
                elif addr >= len(self.memory.ram):
                    print(f"ERROR LDR: Address 0x{addr:04X} out of bounds (memory_size=0x{len(self.memory.ram):04X})")
                    print(f"  Memory size: {len(self.memory.ram)}, required: >= 0x{addr + 1:04X}")
                    mem_val = 0
                else:
                    # Читаем значение из памяти напрямую
                    raw_val = self.memory.ram[addr]
                    mem_val = int(raw_val) & 0xFFFF
                    print(f"DEBUG LDR: rd={rd}, addr=0x{addr:04X}, raw_value={raw_val}, memory[0x{addr:04X}]=0x{mem_val:04X} (decimal {mem_val}), mode={mode1}")
                    print(f"  Memory check: memory.ram exists={self.memory.ram is not None}, length={len(self.memory.ram) if self.memory.ram else 0}")
                
                # Обновляем регистр
                self._update_register(rd, mem_val)
                print(f"DEBUG LDR AFTER: rd={rd}, registers[{rd}]=0x{self.processor.registers[rd]:04X} (decimal {self.processor.registers[rd]}), all_registers={self.processor.registers}")
            else:
                raise Exception(f"LDR requires 2 operands: LDR rd, [address]")
            
        # Формат: LDRR rd, [rs1] - rd = [rs1] (косвенно-регистровая адресация)
        elif instruction == "LDRR":
            if len(operands) >= 2:
                rd, _ = self._parse_operand(operands[0])
                rs1_str = operands[1].strip()
                print(f"DEBUG LDRR PARSE: operands[1]='{rs1_str}'")
                
                # Парсим операнд [rs1] - должен быть косвенно-регистровая адресация
                rs1, mode1 = self._parse_operand(rs1_str)
                print(f"DEBUG LDRR PARSE: rs1={rs1}, mode1={mode1}")
                
                # КРИТИЧНО: Для LDRR операнд [R5] должен быть INDIRECT_REGISTER
                # Но если режим неправильный, исправляем его
                if mode1 != AddressingMode.INDIRECT_REGISTER:
                    # Если операнд начинается с [ и заканчивается на ], и внутри R0-R7
                    if rs1_str.startswith('[') and rs1_str.endswith(']'):
                        inner = rs1_str[1:-1].strip().upper()
                        if inner.startswith('R') and len(inner) >= 2:
                            # Извлекаем номер регистра
                            try:
                                reg_num = int(inner[1:])
                                if 0 <= reg_num <= 7:
                                    rs1 = reg_num
                                    mode1 = AddressingMode.INDIRECT_REGISTER
                                    print(f"DEBUG LDRR PARSE FIX: Исправлен режим адресации, rs1={rs1}, mode1={mode1}")
                            except ValueError:
                                pass
                
                # Получаем адрес из регистра rs1
                # КРИТИЧНО: Для LDRR операнд [R5] означает "прочитать из памяти по адресу, который находится в регистре R5"
                # Поэтому нужно:
                # 1. Получить значение регистра rs1 (это адрес)
                # 2. Прочитать значение из памяти по этому адресу
                
                # Инициализируем переменные
                addr_reg_value = 0
                addr = 0
                mem_val = 0
                
                # Всегда используем REGISTER режим для получения значения регистра (адреса)
                # независимо от того, как был распарсен операнд
                if not self.processor.registers:
                    print(f"ERROR LDRR: Регистры не инициализированы!")
                    mem_val = 0
                elif rs1 < 0 or rs1 >= len(self.processor.registers):
                    print(f"ERROR LDRR: Неверный номер регистра rs1={rs1}, registers_count={len(self.processor.registers)}")
                    mem_val = 0
                else:
                    # Получаем значение регистра rs1 (это адрес)
                    addr_reg_value = self.processor.registers[rs1]
                    print(f"DEBUG LDRR: Получено значение регистра R{rs1}=0x{addr_reg_value:04X} (используется как адрес)")
                    
                    # Ограничиваем адрес 16-битным диапазоном
                    addr = addr_reg_value & 0xFFFF
                    
                    # КРИТИЧНО: Проверяем память ПЕРЕД чтением
                    print(f"DEBUG LDRR START: rs1={rs1}, rs1_value=0x{addr_reg_value:04X}, addr=0x{addr:04X}")
                    print(f"  Memory exists: {self.memory.ram is not None}, length={len(self.memory.ram) if self.memory.ram else 0}")
                    if self.memory.ram and addr >= 0x0100 and addr <= 0x0107:
                        print(f"  DEBUG LDRR: Проверка памяти задачи 1 ПЕРЕД чтением:")
                        for check_addr in [0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107]:
                            if check_addr < len(self.memory.ram):
                                check_val = self.memory.ram[check_addr]
                                print(f"    memory.ram[0x{check_addr:04X}] = {check_val} (0x{check_val:04X})")
                    
                    # Проверяем, что адрес в пределах памяти
                    if addr < 0:
                        print(f"ERROR LDRR: Negative address 0x{addr:04X}")
                        mem_val = 0
                    elif not self.memory.ram:
                        print(f"ERROR LDRR: Память не инициализирована!")
                        mem_val = 0
                    elif addr >= len(self.memory.ram):
                        print(f"ERROR LDRR: Address 0x{addr:04X} out of bounds (memory_size=0x{len(self.memory.ram):04X})")
                        print(f"  Memory size: {len(self.memory.ram)}, required: >= 0x{addr + 1:04X}")
                        mem_val = 0
                    else:
                        # Читаем значение из памяти напрямую
                        raw_val = self.memory.ram[addr]
                        mem_val = int(raw_val) & 0xFFFF
                        print(f"DEBUG LDRR: rd={rd}, rs1={rs1}, rs1_value=0x{addr_reg_value:04X}, addr=0x{addr:04X}, raw_value={raw_val}, memory[0x{addr:04X}]=0x{mem_val:04X} (decimal {mem_val})")
                        print(f"  Memory check: memory.ram exists={self.memory.ram is not None}, length={len(self.memory.ram) if self.memory.ram else 0}")
                        # Дополнительная проверка для задачи 1
                        if addr >= 0x0100 and addr <= 0x0107:
                            print(f"  DEBUG LDRR TASK1: Читаем из адреса 0x{addr:04X}, значение={mem_val} (0x{mem_val:04X})")
                            if mem_val == 0:
                                print(f"  WARNING LDRR TASK1: Прочитано 0 из адреса 0x{addr:04X}, но ожидалось значение элемента массива!")
                                print(f"  WARNING LDRR TASK1: Проверяем все адреса задачи 1:")
                                for check_addr in [0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107]:
                                    if check_addr < len(self.memory.ram):
                                        check_val = self.memory.ram[check_addr]
                                        print(f"    memory.ram[0x{check_addr:04X}] = {check_val} (0x{check_val:04X})")
                
                # Обновляем регистр
                self._update_register(rd, mem_val)
                print(f"DEBUG LDRR AFTER: rd={rd}, registers[{rd}]=0x{self.processor.registers[rd]:04X} (decimal {self.processor.registers[rd]}), all_registers={self.processor.registers}")
            else:
                raise Exception(f"LDRR requires 2 operands: LDRR rd, [rs1]")
            
        # Формат: STR rs1, [address] - [address] = rs1
        elif instruction == "STR":
            if len(operands) >= 2:
                rs1, mode_rs1 = self._parse_operand(operands[0])
                addr, mode_addr = self._parse_operand(operands[1])
                val1 = self._get_operand_value(rs1, mode_rs1)
                print(f"DEBUG STR START: rs1={rs1}, mode_rs1={mode_rs1}, rs1_value=0x{val1:04X} (decimal {val1}), addr=0x{addr:04X}, mode_addr={mode_addr}")
                print(f"  Memory before STR: exists={self.memory.ram is not None}, length={len(self.memory.ram) if self.memory.ram else 0}")
                if self.memory.ram and addr < len(self.memory.ram):
                    old_val = self.memory.ram[addr]
                    print(f"  Memory[0x{addr:04X}] before STR: 0x{old_val:04X} (decimal {old_val})")
                self._set_operand_value(addr, val1, mode_addr)
                # Проверяем, что данные действительно записались
                if self.memory.ram and addr < len(self.memory.ram):
                    new_val = self.memory.ram[addr]
                    print(f"DEBUG STR AFTER: Memory[0x{addr:04X}] after STR: 0x{new_val:04X} (decimal {new_val}), expected=0x{val1:04X}")
                    if new_val != (val1 & 0xFFFF):
                        print(f"ERROR STR: Данные не записались! Ожидалось 0x{val1:04X}, получено 0x{new_val:04X}")
                else:
                    print(f"ERROR STR: Адрес 0x{addr:04X} вне границ памяти! size={len(self.memory.ram) if self.memory.ram else 0}")
            else:
                raise Exception(f"STR requires 2 operands: STR rs1, [address]")
            
        # Формат: STRR rs1, [rd] - [rd] = rs1
        elif instruction == "STRR":
            if len(operands) >= 2:
                rs1, mode_rs1 = self._parse_operand(operands[0])
                rd, mode_rd = self._parse_operand(operands[1])
                val1 = self._get_operand_value(rs1, mode_rs1)
                self._set_operand_value(rd, val1, mode_rd)
            else:
                raise Exception(f"STRR requires 2 operands: STRR rs1, [rd]")
            
        # Формат: CMP rs1, rs2 - сравнить rs1 и rs2 (устанавливает флаги)
        elif instruction == "CMP":
            if len(operands) >= 2:
                rs1, mode1 = self._parse_operand(operands[0])
                rs2, mode2 = self._parse_operand(operands[1])
                val1 = self._get_operand_value(rs1, mode1)
                val2 = self._get_operand_value(rs2, mode2)
                result = val1 - val2
                self.update_flags(result)
            else:
                raise Exception(f"CMP requires 2 operands: CMP rs1, rs2")
        
        # Формат: JMP address - безусловный переход
        elif instruction == "JMP":
            if len(operands) >= 1:
                addr, mode1 = self._parse_operand(operands[0])
                if mode1 == AddressingMode.IMMEDIATE:
                    self.processor.program_counter = addr
                else:
                    self.processor.program_counter = self._get_operand_value(addr, mode1)
            else:
                raise Exception(f"JMP requires 1 operand: JMP address")
            return  # Не увеличиваем PC
        
        # Формат: JZ address - переход если Z=1
        elif instruction == "JZ":
            if len(operands) >= 1:
                if self.processor.flags["zero"]:
                    addr, mode1 = self._parse_operand(operands[0])
                    if mode1 == AddressingMode.IMMEDIATE:
                        self.processor.program_counter = addr
                    else:
                        self.processor.program_counter = self._get_operand_value(addr, mode1)
                    return
            else:
                raise Exception(f"JZ requires 1 operand: JZ address")
        
        # Формат: JNZ address - переход если Z=0
        elif instruction == "JNZ":
            if len(operands) >= 1:
                if not self.processor.flags["zero"]:
                    addr, mode1 = self._parse_operand(operands[0])
                    if mode1 == AddressingMode.IMMEDIATE:
                        self.processor.program_counter = addr
                    else:
                        self.processor.program_counter = self._get_operand_value(addr, mode1)
                    return
            else:
                raise Exception(f"JNZ requires 1 operand: JNZ address")
                
        # Формат: JC address - переход если C=1
        elif instruction == "JC":
            if len(operands) >= 1:
                if self.processor.flags["carry"]:
                    addr, mode1 = self._parse_operand(operands[0])
                    if mode1 == AddressingMode.IMMEDIATE:
                        self.processor.program_counter = addr
                    else:
                        self.processor.program_counter = self._get_operand_value(addr, mode1)
                    return
            else:
                raise Exception(f"JC requires 1 operand: JC address")
                
        # Формат: JNC address - переход если C=0
        elif instruction == "JNC":
            if len(operands) >= 1:
                if not self.processor.flags["carry"]:
                    addr, mode1 = self._parse_operand(operands[0])
                    if mode1 == AddressingMode.IMMEDIATE:
                        self.processor.program_counter = addr
                    else:
                        self.processor.program_counter = self._get_operand_value(addr, mode1)
                    return
            else:
                raise Exception(f"JNC requires 1 operand: JNC address")
        
        elif instruction == "HALT":
            self.processor.is_halted = True
            return
        
        elif instruction == "NOP":
            pass
        
        # Увеличиваем счетчик команд, если не было перехода
        self.processor.program_counter += 1
    
    def step(self) -> bool:
        """Выполнить один шаг программы (одну фазу: fetch, decode или execute)"""
        if self.processor.is_halted:
            return False
        
        # КРИТИЧНО: Убеждаемся, что память инициализирована перед выполнением шага
        if not self.memory.ram:
            min_size = max(0x0200, self.memory_size)
            self.memory.ram = [0] * min_size
            print(f"DEBUG step: Память не инициализирована, создана память размером {min_size}")
        
        # Определяем текущую фазу выполнения
        # Если нет сохраненной команды, начинаем с fetch
        if self._current_instruction_line is None:
            # ФАЗА FETCH: читаем команду из compiled_code[pc]
            if not self.compiled_code or self.processor.program_counter >= len(self.compiled_code):
                self.processor.is_halted = True
                return False
            
            # Читаем команду из памяти команд
            self._current_instruction_line = self.compiled_code[self.processor.program_counter]
            
            # Убеждаемся, что регистры инициализированы
            if not self.processor.registers:
                self.processor.registers = [0] * 8
            while len(self.processor.registers) < 8:
                self.processor.registers.append(0)
            
            # Сохраняем состояние регистров ДО fetch (регистры НЕ меняются в fetch)
            registers_before = [int(r) & 0xFFFF for r in self.processor.registers[:8]]
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            
            # Загружаем команду в IR
            self.processor.current_command = self._current_instruction_line
            self.processor.instruction_register_asm = self._current_instruction_line
            
            # Сохраняем в историю с фазой fetch
            registers_before_final = [int(r) & 0xFFFF for r in registers_before[:8]] if registers_before else [0] * 8
            while len(registers_before_final) < 8:
                registers_before_final.append(0)
            registers_before_final = registers_before_final[:8]
            
            # Сохраняем состояние RAM на момент fetch
            ram_state = list(self.memory.ram) if self.memory.ram else []
            
            history_entry = {
                'command': str(self._current_instruction_line).strip(),
                'instruction': '',
                'operands': [],
                'execution_phase': 'fetch',
                'registers_before': registers_before_final,
                'registers_after': registers_before_final.copy(),  # В fetch регистры не меняются
                'registers': registers_before_final.copy(),
                'ram': ram_state.copy(),  # Состояние RAM на момент fetch
                'ram_before': ram_state.copy(),
                'ram_after': ram_state.copy(),  # В fetch RAM не меняется
                'flags_before': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'flags_after': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'flags': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'programCounter': int(pc_before),
                'programCounter_before': int(pc_before)
            }
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🔵 ФАЗА FETCH | PC=0x{pc_before:04X} | Команда: {self._current_instruction_line}")
            print(f"   Регистры: {registers_before_final}")
            print(f"═══════════════════════════════════════════════════════════════")
            self.memory.history.append(history_entry)
            return True
                
        # Если команда загружена, но не распарсена, переходим к decode
        elif self._current_instruction is None:
            # ФАЗА DECODE: парсим команду и операнды
            instruction_line = self._current_instruction_line
            parts = instruction_line.replace(',', ' ').split()
            self._current_instruction = parts[0]
            self._current_operands = [p.strip() for p in parts[1:] if p.strip()] if len(parts) > 1 else []
            
            # Устанавливаем опкод команды в IR
            if self._current_instruction in self.instructions:
                self.processor.instruction_register = self.instructions[self._current_instruction]
            else:
                self.processor.instruction_register = 0
            
            # Убеждаемся, что регистры инициализированы
            if not self.processor.registers:
                self.processor.registers = [0] * 8
            while len(self.processor.registers) < 8:
                self.processor.registers.append(0)
            
            # Сохраняем состояние регистров ДО decode (регистры НЕ меняются в decode)
            registers_before = [int(r) & 0xFFFF for r in self.processor.registers[:8]]
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            
            # Сохраняем в историю с фазой decode
            registers_before_final = [int(r) & 0xFFFF for r in registers_before[:8]] if registers_before else [0] * 8
            while len(registers_before_final) < 8:
                registers_before_final.append(0)
            registers_before_final = registers_before_final[:8]
            
            # Сохраняем состояние RAM на момент decode
            ram_state = list(self.memory.ram) if self.memory.ram else []
            
            history_entry = {
                'command': str(instruction_line).strip(),
                'instruction': str(self._current_instruction).strip(),
                'operands': [str(op).strip() for op in self._current_operands] if self._current_operands else [],
                'execution_phase': 'decode',
                'registers_before': registers_before_final,
                'registers_after': registers_before_final.copy(),  # В decode регистры не меняются
                'registers': registers_before_final.copy(),
                'ram': ram_state.copy(),  # Состояние RAM на момент decode
                'ram_before': ram_state.copy(),
                'ram_after': ram_state.copy(),  # В decode RAM не меняется
                'flags_before': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'flags_after': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'flags': {
                    'zero': bool(flags_before.get('zero', False)),
                    'carry': bool(flags_before.get('carry', False)),
                    'overflow': bool(flags_before.get('overflow', False)),
                    'negative': bool(flags_before.get('negative', False))
                },
                'programCounter': int(pc_before),
                'programCounter_before': int(pc_before)
            }
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🟡 ФАЗА DECODE | PC=0x{pc_before:04X} | Инструкция: {self._current_instruction} | Операнды: {self._current_operands}")
            print(f"   Регистры: {registers_before_final}")
            print(f"═══════════════════════════════════════════════════════════════")
            self.memory.history.append(history_entry)
            return True
                
        else:
            # ФАЗА EXECUTE: выполняем команду
            instruction = self._current_instruction
            operands = self._current_operands
            instruction_line = self._current_instruction_line
            
            # Убеждаемся, что регистры инициализированы
            if not self.processor.registers:
                self.processor.registers = [0] * 8
            while len(self.processor.registers) < 8:
                self.processor.registers.append(0)
            
            # КРИТИЧНО: Сохраняем состояние регистров и RAM ПЕРЕД выполнением
            registers_before = [int(r) & 0xFFFF for r in self.processor.registers[:8]]
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            ram_before_state = list(self.memory.ram) if self.memory.ram else []  # Сохраняем RAM ДО выполнения
            
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🟢 ФАЗА EXECUTE | PC=0x{pc_before:04X} | Инструкция: {instruction} | Операнды: {operands}")
            print(f"   Регистры ДО: {registers_before}")
            
            # Выполняем инструкцию
            try:
                self.execute_instruction(instruction, operands)
                self.processor.cycles += 1
                
                # КРИТИЧНО: Сохраняем состояние регистров и RAM ПОСЛЕ выполнения
                if not self.processor.registers:
                    self.processor.registers = [0] * 8
                while len(self.processor.registers) < 8:
                    self.processor.registers.append(0)
                registers_after = [int(r) & 0xFFFF for r in self.processor.registers[:8]]
                flags_after = dict(self.processor.flags)
                pc_after = self.processor.program_counter
                ram_after_state = list(self.memory.ram) if self.memory.ram else []  # Сохраняем RAM ПОСЛЕ выполнения
                
                # Проверяем, изменились ли регистры
                registers_changed = registers_before != registers_after
                if registers_changed:
                    changed_regs = []
                    for i in range(8):
                        if registers_before[i] != registers_after[i]:
                            changed_regs.append(f"R{i}: 0x{registers_before[i]:04X} → 0x{registers_after[i]:04X}")
                    print(f"   Регистры ПОСЛЕ: {registers_after}")
                    print(f"   ⚠️ ИЗМЕНЕНЫ: {', '.join(changed_regs)}")
                else:
                    print(f"   Регистры ПОСЛЕ: {registers_after} (не изменились)")
                print(f"   PC: 0x{pc_before:04X} → 0x{pc_after:04X}")
                print(f"═══════════════════════════════════════════════════════════════")
                
                # Обновляем IR для следующей команды (если программа не остановлена)
                if not self.processor.is_halted and pc_after < len(self.compiled_code):
                    next_instruction_line = self.compiled_code[pc_after]
                    next_parts = next_instruction_line.replace(',', ' ').split()
                    next_instruction = next_parts[0] if next_parts else ""
                    self.processor.current_command = next_instruction_line
                    self.processor.instruction_register_asm = next_instruction_line
                    if next_instruction in self.instructions:
                        self.processor.instruction_register = self.instructions[next_instruction]
                    else:
                        self.processor.instruction_register = 0
                
                # Сохраняем состояние в историю с фазой execute
                registers_before_final = [int(r) & 0xFFFF for r in registers_before[:8]] if registers_before else [0] * 8
                registers_after_final = [int(r) & 0xFFFF for r in registers_after[:8]] if registers_after else [0] * 8
                while len(registers_before_final) < 8:
                    registers_before_final.append(0)
                while len(registers_after_final) < 8:
                    registers_after_final.append(0)
                registers_before_final = registers_before_final[:8]
                registers_after_final = registers_after_final[:8]
                
                # ram_before_state и ram_after_state уже сохранены выше
                
                history_entry = {
                    'command': str(instruction_line).strip(),
                    'instruction': str(instruction).strip(),
                    'operands': [str(op).strip() for op in operands] if operands else [],
                    'execution_phase': 'execute',
                    'registers_before': registers_before_final,
                    'registers_after': registers_after_final,
                    'registers': registers_after_final,
                    'ram': ram_after_state.copy(),  # Состояние RAM после выполнения
                    'ram_before': ram_before_state.copy(),  # Состояние RAM до выполнения
                    'ram_after': ram_after_state.copy(),  # Состояние RAM после выполнения
                    'flags_before': {
                        'zero': bool(flags_before.get('zero', False)),
                        'carry': bool(flags_before.get('carry', False)),
                        'overflow': bool(flags_before.get('overflow', False)),
                        'negative': bool(flags_before.get('negative', False))
                    },
                    'flags_after': {
                        'zero': bool(flags_after.get('zero', False)),
                        'carry': bool(flags_after.get('carry', False)),
                        'overflow': bool(flags_after.get('overflow', False)),
                        'negative': bool(flags_after.get('negative', False))
                    },
                    'flags': {
                        'zero': bool(flags_after.get('zero', False)),
                        'carry': bool(flags_after.get('carry', False)),
                        'overflow': bool(flags_after.get('overflow', False)),
                        'negative': bool(flags_after.get('negative', False))
                    },
                    'programCounter': int(pc_after),
                    'programCounter_before': int(pc_before)
                }
                self.memory.history.append(history_entry)
                
                # Сбрасываем промежуточные переменные для следующей команды
                self._current_instruction_line = None
                self._current_instruction = None
                self._current_operands = None
                
                return not self.processor.is_halted
                
            except Exception as e:
                self.processor.is_halted = True
                self.processor.current_command = f"ERROR: {str(e)}"
                # Сбрасываем промежуточные переменные
                self._current_instruction_line = None
                self._current_instruction = None
                self._current_operands = None
                return False
    
    def load_program(self, compiled_code: List[str], source_code: str = ""):
        """Загрузить скомпилированную программу"""
        self.compiled_code = compiled_code
        self.source_code = source_code
        self.processor.program_counter = 0
        self.processor.is_halted = False
        
        # Очищаем историю выполнения (все execution_phase из предыдущих записей удаляются)
        # После очистки истории execution_phase будет None (так как история пустая)
        self.memory.history = []
        
        # Сбрасываем промежуточные переменные для системы фаз выполнения
        # Это гарантирует, что следующий вызов step() начнет с фазы fetch
        self._current_instruction_line = None
        self._current_instruction = None
        self._current_operands = None
        
        # Сбрасываем регистры в начальное состояние (все нули)
        self.processor.registers = [0] * 8
        # Сбрасываем флаги
        self.processor.flags = {
            "zero": False,
            "carry": False,
            "overflow": False,
            "negative": False
        }
        # Сбрасываем счетчик циклов
        self.processor.cycles = 0
        
        # Инициализируем IR первой командой программы
        if compiled_code and len(compiled_code) > 0:
            first_instruction_line = compiled_code[0]
            first_parts = first_instruction_line.replace(',', ' ').split()
            first_instruction = first_parts[0] if first_parts else ""
            self.processor.current_command = first_instruction_line
            self.processor.instruction_register_asm = first_instruction_line
            if first_instruction in self.instructions:
                self.processor.instruction_register = self.instructions[first_instruction]
            else:
                self.processor.instruction_register = 0
        else:
            self.processor.current_command = ""
            self.processor.instruction_register_asm = ""
            self.processor.instruction_register = 0
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние процессора"""
        # Проверяем память перед сериализацией (для отладки задачи 1)
        if self.memory.ram and len(self.memory.ram) > 0x0100:
            check_val = self.memory.ram[0x0100]
            if check_val != 0:
                print(f"DEBUG get_state: Память содержит данные, ram[0x0100]={check_val} (0x{check_val:04X}), size={len(self.memory.ram)}")
        
        # КРИТИЧНО: Убеждаемся, что память инициализирована перед сериализацией
        if not self.memory.ram:
            print(f"WARNING get_state: Память не инициализирована, создаем пустую память")
            self.memory.ram = [0] * self.memory_size
        
        # Гарантируем, что история правильно сериализуется
        # Преобразуем каждый элемент истории, чтобы убедиться, что все значения - это базовые типы Python
        history_serialized = []
        for entry in self.memory.history:
            history_entry = {}
            for key, value in entry.items():
                if key in ['registers_before', 'registers_after', 'registers']:
                    # Преобразуем регистры в список целых чисел
                    if isinstance(value, list) and len(value) > 0:
                        # Преобразуем каждый элемент в int и ограничиваем 16-битным диапазоном
                        regs = [int(r) & 0xFFFF for r in value]
                        # Гарантируем, что у нас есть ровно 8 регистров
                        while len(regs) < 8:
                            regs.append(0)
                        history_entry[key] = regs[:8]
                    else:
                        history_entry[key] = [0] * 8
                elif key in ['flags_before', 'flags_after', 'flags']:
                    # Преобразуем флаги в словарь с булевыми значениями
                    if isinstance(value, dict):
                        history_entry[key] = {
                            'zero': bool(value.get('zero', False)),
                            'carry': bool(value.get('carry', False)),
                            'overflow': bool(value.get('overflow', False)),
                            'negative': bool(value.get('negative', False))
                        }
                    else:
                        history_entry[key] = {'zero': False, 'carry': False, 'overflow': False, 'negative': False}
                elif key == 'execution_phase':
                    # Сериализуем execution_phase как строку
                    print(f"DEBUG get_state: execution_phase serialization: key={key}, value={value} (type={type(value)}), result={value}")
                    history_entry[key] = str(value) if value is not None else None
                else:
                    # Для остальных полей просто копируем значение
                    history_entry[key] = value
            history_serialized.append(history_entry)
        
        return {
            "processor": {
                "registers": [int(r) & 0xFFFF for r in self.processor.registers] if self.processor.registers else [0] * 8,
                "program_counter": self.processor.program_counter,
                "instruction_register": self.processor.instruction_register,
                "instruction_register_asm": self.processor.instruction_register_asm,
                "flags": {
                    'zero': bool(self.processor.flags.get('zero', False)),
                    'carry': bool(self.processor.flags.get('carry', False)),
                    'overflow': bool(self.processor.flags.get('overflow', False)),
                    'negative': bool(self.processor.flags.get('negative', False))
                },
                "current_command": self.processor.current_command,
                "is_halted": self.processor.is_halted,
                "cycles": self.processor.cycles
            },
            "memory": {
                # КРИТИЧНО: Создаем новый список для сериализации, чтобы Pydantic видел изменения
                # Убеждаемся, что память инициализирована
                "ram": [int(r) & 0xFFFF for r in (self.memory.ram if self.memory.ram else [])],  # 16-битные значения
                "history": history_serialized
            },
            "source_code": self.source_code,
            "machine_code": self.compiled_code,
            "current_task": None
        }