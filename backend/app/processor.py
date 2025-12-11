"""
Эмулятор одноадресного процессора с архитектурой Фон-Неймана
"""
from typing import List, Dict, Any, Optional, Tuple
from .models import ProcessorState, MemoryState, AddressingMode, InstructionField

class RISCProcessor:
    """Эмулятор одноадресного процессора Фон-Неймана"""
    
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
        
        # Система команд одноадресного процессора (ACC + один операнд)
        self.instructions = {
            # Арифметико-логические команды
            'ADD': 0x01,    # ADD operand - ACC = ACC + operand
            'SUB': 0x02,    # SUB operand - ACC = ACC - operand
            'MUL': 0x03,    # MUL operand - ACC = ACC * operand
            'DIV': 0x04,    # DIV operand - ACC = ACC / operand
            'AND': 0x05,    # AND operand - ACC = ACC & operand
            'OR':  0x06,    # OR  operand - ACC = ACC | operand
            'XOR': 0x07,    # XOR operand - ACC = ACC ^ operand
            'NOT': 0x08,    # NOT         - ACC = ~ACC
            
            # Команды пересылки данных
            'LDA': 0x10,    # LDA operand - ACC = operand (загрузка в аккумулятор)
            'STA': 0x11,    # STA operand - [operand] = ACC (сохранение из аккумулятора)
            'LDI': 0x12,    # LDI imm     - ACC = immediate (непосредственная загрузка)
            
            # Команды сравнения и переходов
            'CMP': 0x20,    # CMP operand - сравнить ACC и operand
            'JMP': 0x21,    # JMP addr    - безусловный переход
            'JZ':  0x22,    # JZ addr     - переход если Z=1
            'JNZ': 0x23,    # JNZ addr    - переход если Z=0
            'JC':  0x24,    # JC addr     - переход если C=1
            'JNC': 0x25,    # JNC addr    - переход если C=0
            'JV':  0x26,    # JV addr     - переход если V=1
            'JNV': 0x27,    # JNV addr    - переход если V=0
            'JN':  0x28,    # JN addr     - переход если N=1
            'JNN': 0x29,    # JNN addr    - переход если N=0
            
            # Системные команды
            'HALT': 0xFF,   # HALT        - остановка
            'NOP':  0x00,   # NOP         - нет операции
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
    
    def _parse_operand(self, operand_str: str) -> Tuple[Any, AddressingMode]:
        """Парсинг операнда с определением типа адресации (одноадресная архитектура)
        
        Форматы:
        - Непосредственное значение: LDA 100 (десятичное число без префикса)
        - Прямой адрес: LDA [0x0100] или LDA 0x0100 (hex с префиксом 0x)
        """
        operand_str = operand_str.strip()
        
        # Прямая адресация [address] - всегда прямой адрес памяти
        if operand_str.startswith('[') and operand_str.endswith(']'):
            inner = operand_str[1:-1].strip()
            addr = self._parse_number(inner)
            print(f"DEBUG _parse_operand: operand_str='{operand_str}', inner='{inner}', addr=0x{addr:04X}, mode=DIRECT")
            return addr, AddressingMode.DIRECT
        
        # Шестнадцатеричное число (0x...) - прямой адрес памяти
        if operand_str.startswith('0x') or operand_str.startswith('0X'):
            addr = self._parse_number(operand_str)
            print(f"DEBUG _parse_operand: operand_str='{operand_str}', addr=0x{addr:04X}, mode=DIRECT (hex адрес)")
            return addr, AddressingMode.DIRECT
        
        # Десятичное число (без префикса) - непосредственное значение
        if operand_str.isdigit() or (operand_str.startswith('-') and operand_str[1:].isdigit()):
            val = self._parse_number(operand_str)
            print(f"DEBUG _parse_operand: operand_str='{operand_str}', value={val}, mode=IMMEDIATE (decimal)")
            return val, AddressingMode.IMMEDIATE
        
        # Метка (для переходов) - будет разрешена позже
        return operand_str, AddressingMode.IMMEDIATE
    
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
    
    def _decode_instruction(self, instruction: int) -> InstructionField:
        """Декодирование инструкции для отображения полей (одноадресная архитектура)"""
        if instruction > 0xFFFF:  # 32-битная команда (для LDI с непосредственным значением)
            immediate = instruction >> 16
            opcode = (instruction >> 12) & 0xF
            operand = immediate  # Для 32-битного формата операнд = непосредственное значение
            addressing_mode = AddressingMode.IMMEDIATE
        else:  # 16-битная команда
            opcode = (instruction >> 12) & 0xF
            operand = instruction & 0xFFF  # [11:0] - адрес или значение
            # По умолчанию считаем адресом памяти (DIRECT)
            # Для точного определения нужен контекст команды
            addressing_mode = AddressingMode.DIRECT if operand != 0 else AddressingMode.IMMEDIATE
            immediate = 0
        
        # Определяем тип команды
        instruction_type = "I" if operand != 0 or immediate != 0 else "S"
        
        return InstructionField(
            opcode=opcode,
            opcode_bits=format(opcode, '04b'),
            operand=operand if operand != 0 else immediate,
            operand_bits=format(operand, '012b') if operand != 0 else (format(immediate, '016b') if immediate != 0 else ""),
            immediate=immediate,
            immediate_bits=format(immediate, '016b') if immediate != 0 else "",
            addressing_mode=addressing_mode,
            instruction_type=instruction_type
        )
    
    def _get_operand_value(self, operand: Any, addressing_mode: AddressingMode) -> int:
        """Получение значения операнда в зависимости от режима адресации (одноадресная архитектура)"""
        if addressing_mode == AddressingMode.IMMEDIATE:
            return operand
        elif addressing_mode == AddressingMode.DIRECT:
            if 0 <= operand < len(self.memory.ram):
                value = self.memory.ram[operand]
                print(f"DEBUG _get_operand_value DIRECT: operand=0x{operand:04X}, value=0x{value:04X}, memory[0x{operand:04X}]=0x{value:04X}")
                return value
            print(f"DEBUG _get_operand_value DIRECT: operand=0x{operand:04X} OUT_OF_BOUNDS (memory_size=0x{len(self.memory.ram):04X})")
            return 0
        return 0
    
    def _set_operand_value(self, operand: Any, value: int, addressing_mode: AddressingMode):
        """Установка значения операнда в зависимости от режима адресации (одноадресная архитектура)"""
        if addressing_mode == AddressingMode.DIRECT:
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
    
    def _update_accumulator(self, value: int):
        """Обновить аккумулятор значением value"""
        self.processor.accumulator = int(value) & 0xFFFF
        print(f"DEBUG _update_accumulator: ACC = 0x{self.processor.accumulator:04X} (decimal {self.processor.accumulator})")
    
    def execute_instruction(self, instruction: str, operands: List[str] = None):
        """Выполнение одной инструкции (одноадресная архитектура)"""
        instruction = instruction.upper().strip()
        operands = operands or []
        
        if instruction not in self.instructions:
            raise Exception(f"Unknown instruction: {instruction}")
        
        # Арифметические операции: операнд всегда адрес памяти
        # Формат: ADD addr - ACC = ACC + память[addr]
        if instruction == "ADD":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                # Арифметические операции работают только с памятью
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"ADD requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator + val
                result = int(result) & 0xFFFF
                self.update_flags(result, "add")
                self._update_accumulator(result)
                print(f"DEBUG ADD: ACC={self.processor.accumulator:04X}, memory[0x{operand:04X}]={val:04X}, result={result:04X}")
            else:
                raise Exception(f"ADD requires 1 operand: ADD addr")
        
        # Формат: SUB addr - ACC = ACC - память[addr]
        elif instruction == "SUB":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"SUB requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator - val
                result = result & 0xFFFF
                self.update_flags(result, "sub")
                self._update_accumulator(result)
            else:
                raise Exception(f"SUB requires 1 operand: SUB addr")
        
        # Формат: MUL addr - ACC = ACC * память[addr]
        elif instruction == "MUL":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"MUL requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator * val
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_accumulator(result)
            else:
                raise Exception(f"MUL requires 1 operand: MUL addr")
        
        # Формат: DIV addr - ACC = ACC / память[addr]
        elif instruction == "DIV":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"DIV requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                if val == 0:
                    raise Exception("Division by zero")
                result = self.processor.accumulator // val
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_accumulator(result)
            else:
                raise Exception(f"DIV requires 1 operand: DIV addr")
            
        # Логические операции: операнд всегда адрес памяти
        # Формат: AND addr - ACC = ACC & память[addr]
        elif instruction == "AND":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"AND requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator & val
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_accumulator(result)
            else:
                raise Exception(f"AND requires 1 operand: AND addr")
            
        # Формат: OR addr - ACC = ACC | память[addr]
        elif instruction == "OR":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"OR requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator | val
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_accumulator(result)
            else:
                raise Exception(f"OR requires 1 operand: OR addr")
            
        # Формат: XOR addr - ACC = ACC ^ память[addr]
        elif instruction == "XOR":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"XOR requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator ^ val
                result = result & 0xFFFF
                self.update_flags(result)
                self._update_accumulator(result)
            else:
                raise Exception(f"XOR requires 1 operand: XOR addr")
            
        # Формат: NOT - ACC = ~ACC
        elif instruction == "NOT":
            result = ~self.processor.accumulator
            result = result & 0xFFFF
            self.update_flags(result)
            self._update_accumulator(result)
            
        # Команды загрузки и сохранения
        # Формат: LDA addr - ACC = память[addr] (загрузка из памяти)
        elif instruction == "LDA":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                # LDA всегда работает с адресом памяти
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"LDA requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                val = int(val) & 0xFFFF
                self._update_accumulator(val)
                print(f"DEBUG LDA: ACC={self.processor.accumulator:04X}, memory[0x{operand:04X}]={val:04X}")
            else:
                raise Exception(f"LDA requires 1 operand: LDA addr")
            
        # Формат: STA addr - память[addr] = ACC (сохранение в память)
        elif instruction == "STA":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"STA requires DIRECT addressing mode (memory address), got {mode}")
                val = self.processor.accumulator
                self._set_operand_value(operand, val, mode)
                print(f"DEBUG STA: memory[0x{operand:04X}] = ACC={val:04X}")
            else:
                raise Exception(f"STA requires 1 operand: STA addr")
            
        # Формат: LDI imm - ACC = imm (непосредственная загрузка константы)
        elif instruction == "LDI":
            if len(operands) >= 1:
                imm, mode = self._parse_operand(operands[0])
                # LDI всегда работает с непосредственным значением
                if mode != AddressingMode.IMMEDIATE:
                    raise Exception(f"LDI requires IMMEDIATE addressing mode (constant value), got {mode}")
                imm = int(imm) & 0xFFFF
                self._update_accumulator(imm)
                print(f"DEBUG LDI: ACC={self.processor.accumulator:04X}, imm={imm:04X}")
            else:
                raise Exception(f"LDI requires 1 operand: LDI imm")
            
        # Команды сравнения: операнд всегда адрес памяти
        # Формат: CMP addr - установить флаги на основе (ACC - память[addr])
        elif instruction == "CMP":
            if len(operands) >= 1:
                operand, mode = self._parse_operand(operands[0])
                if mode != AddressingMode.DIRECT:
                    raise Exception(f"CMP requires DIRECT addressing mode (memory address), got {mode}")
                val = self._get_operand_value(operand, mode)
                result = self.processor.accumulator - val
                self.update_flags(result)
            else:
                raise Exception(f"CMP requires 1 operand: CMP addr")
        
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
            
            # Сохраняем состояние аккумулятора ДО fetch (аккумулятор НЕ меняется в fetch)
            accumulator_before = int(self.processor.accumulator) & 0xFFFF
            registers_before = [accumulator_before]  # Для совместимости с историей
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            
            # Загружаем команду в IR
            self.processor.current_command = self._current_instruction_line
            self.processor.instruction_register_asm = self._current_instruction_line
            
            # Определяем опкод команды для IR
            parts = self._current_instruction_line.replace(',', ' ').split()
            instruction_name = parts[0] if parts else ""
            ir_value = self.instructions.get(instruction_name, 0)
            self.processor.instruction_register = ir_value
            
            # Сохраняем в историю с фазой fetch
            registers_before_final = registers_before if registers_before else [0]
            
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
                'programCounter_before': int(pc_before),
                'programCounter_after': int(pc_before),  # В fetch PC не меняется
                'instruction_register': int(ir_value) & 0xFFFF,
                'instruction_register_asm': str(self._current_instruction_line).strip()
            }
            # Форматируем аккумулятор для вывода
            acc_str = f"ACC=0x{accumulator_before:04X}({accumulator_before})"
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🔵 ФАЗА FETCH | PC=0x{pc_before:04X} | Команда: {self._current_instruction_line}")
            print(f"   {acc_str}")
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
            
            # Сохраняем состояние аккумулятора ДО decode (аккумулятор НЕ меняется в decode)
            accumulator_before = int(self.processor.accumulator) & 0xFFFF
            registers_before = [accumulator_before]  # Для совместимости с историей
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            
            # Сохраняем в историю с фазой decode
            registers_before_final = registers_before if registers_before else [0]
            
            # Сохраняем состояние RAM на момент decode
            ram_state = list(self.memory.ram) if self.memory.ram else []
            
            # Получаем IR и IR_asm
            ir_value = int(self.processor.instruction_register) & 0xFFFF
            ir_asm = str(self.processor.instruction_register_asm) if self.processor.instruction_register_asm else str(instruction_line).strip()
            
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
                'programCounter_before': int(pc_before),
                'programCounter_after': int(pc_before),  # В decode PC не меняется
                'instruction_register': int(ir_value) & 0xFFFF,
                'instruction_register_asm': ir_asm
            }
            # Форматируем аккумулятор для вывода
            acc_str = f"ACC=0x{accumulator_before:04X}({accumulator_before})"
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🟡 ФАЗА DECODE | PC=0x{pc_before:04X} | Инструкция: {self._current_instruction} | Операнды: {self._current_operands}")
            print(f"   {acc_str}")
            print(f"═══════════════════════════════════════════════════════════════")
            self.memory.history.append(history_entry)
            return True
                
        else:
            # ФАЗА EXECUTE: выполняем команду
            instruction = self._current_instruction
            operands = self._current_operands
            instruction_line = self._current_instruction_line
            
            # КРИТИЧНО: Сохраняем состояние аккумулятора и RAM ПЕРЕД выполнением
            accumulator_before = int(self.processor.accumulator) & 0xFFFF
            registers_before = [accumulator_before]  # Для совместимости с историей
            flags_before = dict(self.processor.flags)
            pc_before = self.processor.program_counter
            ram_before_state = list(self.memory.ram) if self.memory.ram else []  # Сохраняем RAM ДО выполнения
            
            # Форматируем аккумулятор ДО выполнения
            acc_before_str = f"ACC=0x{accumulator_before:04X}({accumulator_before})"
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"🟢 ФАЗА EXECUTE | PC=0x{pc_before:04X} | Инструкция: {instruction} | Операнды: {operands}")
            print(f"   {acc_before_str}")
            
            # Выполняем инструкцию
            try:
                self.execute_instruction(instruction, operands)
                self.processor.cycles += 1
                
                # КРИТИЧНО: Сохраняем состояние аккумулятора и RAM ПОСЛЕ выполнения
                accumulator_after = int(self.processor.accumulator) & 0xFFFF
                registers_after = [accumulator_after]  # Для совместимости с историей
                flags_after = dict(self.processor.flags)
                pc_after = self.processor.program_counter
                ram_after_state = list(self.memory.ram) if self.memory.ram else []  # Сохраняем RAM ПОСЛЕ выполнения
                
                # Форматируем аккумулятор ПОСЛЕ выполнения
                acc_after_str = f"ACC=0x{accumulator_after:04X}({accumulator_after})"
                
                # Проверяем, изменился ли аккумулятор
                accumulator_changed = accumulator_before != accumulator_after
                if accumulator_changed:
                    print(f"   {acc_after_str}")
                    print(f"   ⚠️ ИЗМЕНЕН: ACC: 0x{accumulator_before:04X} → 0x{accumulator_after:04X}")
                else:
                    print(f"   {acc_after_str} (не изменился)")
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
                registers_before_final = registers_before if registers_before else [0]
                registers_after_final = registers_after if registers_after else [0]
                
                # ram_before_state и ram_after_state уже сохранены выше
                
                # Получаем IR и IR_asm для execute фазы
                ir_value_before = int(self.processor.instruction_register) & 0xFFFF
                ir_asm = str(self.processor.instruction_register_asm) if self.processor.instruction_register_asm else str(instruction_line).strip()
                
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
                    'programCounter_before': int(pc_before),
                    'programCounter_after': int(pc_after),
                    'instruction_register': int(ir_value_before) & 0xFFFF,
                    'instruction_register_asm': ir_asm
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
        
        # Сбрасываем аккумулятор в начальное состояние
        self.processor.accumulator = 0
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
                    # Преобразуем аккумулятор в список целых чисел (для совместимости)
                    if isinstance(value, list) and len(value) > 0:
                        # Преобразуем каждый элемент в int и ограничиваем 16-битным диапазоном
                        regs = [int(r) & 0xFFFF for r in value]
                        history_entry[key] = regs
                    else:
                        history_entry[key] = [0]
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
                "accumulator": int(self.processor.accumulator) & 0xFFFF,
                "registers": [int(self.processor.accumulator) & 0xFFFF],  # Для совместимости с frontend
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