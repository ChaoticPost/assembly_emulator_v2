"""
Эмулятор двухадресного RISC процессора с архитектурой Фон-Неймана
"""
from typing import List, Dict, Optional, Any
from .processor import RISCProcessor
from .assembler import RISCAssembler
from .tasks import TaskManager
from .models import EmulatorState, ProcessorState, MemoryState
from .processor import RISCProcessor

class RISCEmulator:
    """Эмулятор двухадресного RISC процессора"""
    
    def __init__(self, memory_size: int = 8192):
        self.processor = RISCProcessor(memory_size)
        self.assembler = RISCAssembler()
        self.task_manager = TaskManager()
        self.current_task = None
        self._task_data_write_index = 0  # Счетчик для постепенной записи данных задач

    def reset(self):
        """Сброс эмулятора в начальное состояние"""
        self.processor.reset()
        self.current_task = None
        self._task_data_write_index = 0
    
    def compile_code(self, source_code: str) -> Dict[str, Any]:
        """Компиляция исходного кода"""
        try:
            machine_code, labels = self.assembler.assemble(source_code)
            return {
                "success": True,
                "machine_code": machine_code,
                "labels": labels,
                "message": "Code compiled successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Compilation error: {str(e)}"
            }
    
    def load_program(self, source_code: str):
        """Загрузка программы в эмулятор"""
        compile_result = self.compile_code(source_code)
        if compile_result["success"]:
            self.processor.load_program(compile_result["machine_code"], source_code)
            return True
            return False
    
    def _encode_instruction_to_machine_code(self, instruction_line: str, labels: Dict[str, int] = None) -> int:
        """Кодирование инструкции в машинный код для записи в RAM (одноадресная архитектура)"""
        from .models import AddressingMode
        
        # Парсим строку команды
        parts = instruction_line.replace(',', ' ').split()
        if not parts:
            return 0
        
        instruction = parts[0].upper().strip()
        operands = [p.strip() for p in parts[1:] if p.strip()] if len(parts) > 1 else []
        
        if instruction not in self.processor.instructions:
            return 0
        
        opcode = self.processor.instructions[instruction]
        labels = labels or {}
        
        # Команды без операндов (NOT, HALT, NOP)
        if instruction in ["HALT", "NOP", "NOT"]:
            return self.processor._encode_instruction(opcode, 0, AddressingMode.IMMEDIATE)
        
        # Команды с одним операндом
        if len(operands) >= 1:
            operand_str = operands[0]
            operand_val, operand_mode = self.processor._parse_operand(operand_str)
            
            # Если операнд - метка, заменяем на адрес
            if isinstance(operand_val, str) and operand_val in labels:
                operand_val = labels[operand_val]
                operand_mode = AddressingMode.IMMEDIATE
            elif not isinstance(operand_val, int):
                operand_val = 0
            
            # Команды переходов (JMP, JZ, JNZ, JC, JNC, JV, JNV, JN, JNN) - используют IMMEDIATE для адресов
            if instruction.startswith("J"):
                return self.processor._encode_instruction(opcode, operand_val, AddressingMode.IMMEDIATE)
            
            # Команды загрузки/сохранения и арифметические/логические операции
            # LDI использует IMMEDIATE, остальные - DIRECT для адресов памяти
            if instruction == "LDI":
                return self.processor._encode_instruction(opcode, operand_val, AddressingMode.IMMEDIATE)
            else:
                # LDA, STA, ADD, SUB, MUL, DIV, AND, OR, XOR, CMP используют DIRECT для адресов
                return self.processor._encode_instruction(opcode, operand_val, operand_mode)
        
        # Команда без операнда (по умолчанию)
        return self.processor._encode_instruction(opcode, 0, AddressingMode.IMMEDIATE)
    
    def _write_program_to_ram(self, start_address: int = 0x0000):
        """Запись программы в RAM начиная с указанного адреса (одноадресная архитектура)"""
        if not self.processor.compiled_code:
            return
        
        # Получаем метки из ассемблера
        compile_result = self.compile_code(self.processor.source_code)
        labels = compile_result.get("labels", {}) if compile_result.get("success") else {}
        
        # Подсчитываем общий размер (с учетом 32-битных команд)
        total_size = 0
        for instruction_line in self.processor.compiled_code:
            machine_code = self._encode_instruction_to_machine_code(instruction_line, labels)
            # Если команда больше 16 бит, она занимает 2 ячейки
            if machine_code > 0xFFFF:
                total_size += 2
            else:
                total_size += 1
        
        # Убеждаемся, что RAM достаточно большая
        required_size = start_address + total_size + 1
        if not self.processor.memory.ram or len(self.processor.memory.ram) < required_size:
            new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
            while len(new_ram) < required_size:
                new_ram.append(0)
            self.processor.memory.ram = new_ram
        
        # Записываем команды в RAM
        new_ram = list(self.processor.memory.ram)
        current_addr = start_address
        for instruction_line in self.processor.compiled_code:
            machine_code = self._encode_instruction_to_machine_code(instruction_line, labels)
            
            if machine_code > 0xFFFF:
                # 32-битная команда: записываем два слова
                # [31:16] - старшее слово, [15:0] - младшее слово
                high_word = (machine_code >> 16) & 0xFFFF
                low_word = machine_code & 0xFFFF
                new_ram[current_addr] = low_word
                new_ram[current_addr + 1] = high_word
                print(f"DEBUG _write_program_to_ram: Записана 32-битная команда '{instruction_line}' -> 0x{machine_code:08X} (low=0x{low_word:04X}, high=0x{high_word:04X}) по адресам 0x{current_addr:04X}-0x{current_addr+1:04X}")
                current_addr += 2
            else:
                # 16-битная команда: записываем одно слово
                new_ram[current_addr] = machine_code & 0xFFFF
                print(f"DEBUG _write_program_to_ram: Записана 16-битная команда '{instruction_line}' -> 0x{machine_code:04X} по адресу 0x{current_addr:04X}")
                current_addr += 1
        
        self.processor.memory.ram = new_ram
        print(f"DEBUG _write_program_to_ram: Записано {len(self.processor.compiled_code)} команд в RAM начиная с адреса 0x{start_address:04X}, занято {total_size} ячеек памяти")
    
    def load_task(self, task_id: int) -> Dict[str, Any]:
        """Загрузка задачи"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found",
                "message": f"Task {task_id} not found"
            }
        
        try:
            # Сбрасываем процессор (но НЕ память - данные задачи должны сохраниться)
            # Сохраняем текущую память перед сбросом
            saved_ram = list(self.processor.memory.ram) if self.processor.memory.ram else []
            saved_ram_size = len(saved_ram) if saved_ram else self.processor.memory_size
            
            # Сбрасываем только процессор, но НЕ память
            # Вместо полного reset, сбрасываем только состояние процессора
            self.processor.processor = ProcessorState()
            self.processor.processor.accumulator = 0
            self.processor.processor.program_counter = 0
            self.processor.processor.is_halted = False
            self.processor.processor.flags = {
                "zero": False,
                "carry": False,
                "overflow": False,
                "negative": False
            }
            self.processor.processor.cycles = 0
            self.processor.memory.history = []
            
            # Сбрасываем промежуточные переменные для системы фаз выполнения
            self.processor._current_instruction_line = None
            self.processor._current_instruction = None
            self.processor._current_operands = None
            
            # Восстанавливаем память (гарантируем достаточный размер)
            if saved_ram and len(saved_ram) >= 0x0101:
                # Создаем новый список для Pydantic
                self.processor.memory.ram = list(saved_ram)
            else:
                # Если память пустая или недостаточного размера, создаем новую
                min_size = max(saved_ram_size, 0x0200)  # Минимум до 0x0200
                self.processor.memory.ram = [0] * min_size
                print(f"DEBUG load_task: Создана новая память размером {min_size}")
            
            # Сохраняем память перед загрузкой программы
            ram_before_load_program = list(self.processor.memory.ram) if self.processor.memory.ram else []
            
            # Загружаем программу задачи (это НЕ сбрасывает память, только регистры и историю)
            self.load_program(task["program"])
            
            # Для задачи 2: записываем команды в RAM начиная с адреса 0x0000 (архитектура фон Неймана)
            if task_id == 2:
                self._write_program_to_ram(start_address=0x0000)
            
            # Восстанавливаем память после load_program (на всякий случай)
            # НО для задачи 2 не восстанавливаем, так как мы только что записали команды
            if task_id != 2:
                if ram_before_load_program and len(ram_before_load_program) > 0:
                    self.processor.memory.ram = ram_before_load_program
                    print(f"DEBUG load_task: Память восстановлена после load_program, length={len(self.processor.memory.ram)}")
            
            # Настраиваем данные задачи (ВАЖНО: после load_program, чтобы память не сбросилась)
            # Для задач 1 и 2 НЕ записываем данные в память при загрузке - они будут записаны при первом execute_step
            if task_id == 1 or task_id == 2:
                # Для задач 1 и 2 сохраняем данные задачи, но НЕ записываем их в память
                # Данные будут записаны при первом execute_step перед выполнением команды
                pass
            else:
                self.task_manager.setup_task_data(self.processor, task_id)
            
            # КРИТИЧНО: Для задачи 1 НЕ записываем данные в память при загрузке
            # Данные будут записаны при первом execute_step перед выполнением команды
            if task_id == 1:
                # Получаем ожидаемые данные из test_data задачи для определения размера памяти
                test_data = task["test_data"]
                if test_data and len(test_data) >= 2:
                    size = test_data[0]
                    elements = test_data[1:1 + size]
                    expected_data = [size] + elements  # [размер, элемент1, элемент2, ...]
                    
                    # Вычисляем требуемый размер памяти динамически
                    required_size = 0x0100 + len(expected_data) + 1  # До последнего элемента включительно
                    if len(self.processor.memory.ram) < required_size:
                        print(f"DEBUG load_task: Расширяем память до {required_size} для задачи 1")
                        new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                        while len(new_ram) < required_size:
                            new_ram.append(0)
                        self.processor.memory.ram = new_ram
                    
                    # Очищаем область данных задачи (0x0100 и далее), чтобы данные были записаны только при первом execute_step
                    print(f"DEBUG load_task: Для задачи 1 очищаем память - данные будут записаны при первом execute_step")
                    new_ram = list(self.processor.memory.ram)
                    for i in range(len(expected_data)):
                        addr = 0x0100 + i
                        if addr < len(new_ram):
                            new_ram[addr] = 0
                    self.processor.memory.ram = new_ram
                    print(f"DEBUG load_task: Память очищена для задачи 1, данные будут записаны при первом execute_step")
            
            # КРИТИЧНО: Для задачи 2 НЕ записываем данные в память при загрузке
            # Данные будут записаны при первом execute_step перед выполнением команды
            elif task_id == 2:
                # Получаем ожидаемые данные из test_data задачи для определения размера памяти
                test_data = task["test_data"]
                if test_data and len(test_data) >= 2:
                    # Формат: [size_a, a1..aN, size_b, b1..bM]
                    size_a = test_data[0]
                    a_vals = test_data[1:1 + size_a]
                    size_b = test_data[1 + size_a]
                    b_vals = test_data[2 + size_a:2 + size_a + size_b]
                    
                    # Вычисляем требуемый размер памяти
                    required_size = max(0x020A, 0x030A) + 2
                    if len(self.processor.memory.ram) < required_size:
                        print(f"DEBUG load_task: Расширяем память до {required_size} для задачи 2")
                        new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                        while len(new_ram) < required_size:
                            new_ram.append(0)
                        self.processor.memory.ram = new_ram
                    
                    # Очищаем область данных задачи (0x0200-0x020A и 0x0300-0x030A), чтобы данные были записаны только при первом execute_step
                    print(f"DEBUG load_task: Для задачи 2 очищаем память - данные будут записаны при первом execute_step")
                    new_ram = list(self.processor.memory.ram)
                    # Очищаем массив A (0x0200-0x020A)
                    for i in range(size_a + 1):
                        addr = 0x0200 + i
                        if addr < len(new_ram):
                            new_ram[addr] = 0
                    # Очищаем массив B (0x0300-0x030A)
                    for i in range(size_b + 1):
                        addr = 0x0300 + i
                        if addr < len(new_ram):
                            new_ram[addr] = 0
                    self.processor.memory.ram = new_ram
                    print(f"DEBUG load_task: Память очищена для задачи 2, данные будут записаны при первом execute_step")
            
            self.current_task = task_id
            self._task_data_write_index = 0  # Сбрасываем счетчик при загрузке задачи
            
            return {
                "success": True,
                "state": self.get_state(),
                "task": task,
                "message": f"Task {task_id} loaded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error loading task {task_id}: {str(e)}"
            }
    
    def execute_step(self) -> Dict[str, Any]:
        """Выполнение одного шага программы"""
        try:
            if self.processor.processor.is_halted:
                return {
                    "success": True,
                    "state": self.get_state(),
                    "continues": False,
                    "message": "Program is halted"
                }
            
            # Выполняем одну фазу (fetch/decode/execute)
            continues = self.processor.step()
            
            # Определяем фазу, которая только что отработала
            last_history = self.processor.memory.history[-1] if self.processor.memory.history else None
            last_phase = last_history.get("execution_phase") if isinstance(last_history, dict) else None
            
            # Данные задач пишем ТОЛЬКО после фазы execute первой команды
            if last_phase != "execute":
                return {
                    "success": True,
                    "state": self.get_state(),
                    "continues": continues,
                    "message": "Step executed successfully"
                }
            
            # Удобная функция для обновления последней записи истории RAM,
            # чтобы frontend видел актуальное состояние для hex/dex сразу после записи
            def _update_history_ram(new_ram_snapshot: list):
                if self.processor.memory.history:
                    entry = self.processor.memory.history[-1]
                    if isinstance(entry, dict):
                        entry["ram_after"] = list(new_ram_snapshot)
                        entry["ram"] = list(new_ram_snapshot)
                        self.processor.memory.history[-1] = entry
            
            # Для задач 1 и 2: записываем данные в память постепенно, по одному элементу за execute
            if self.current_task == 1:
                # Получаем данные задачи
                task = self.task_manager.get_task(1)
                if task:
                    test_data = task["test_data"]
                    if test_data and len(test_data) >= 2:
                        size = test_data[0]
                        elements = test_data[1:1 + size]
                        expected_data = [size] + elements  # [размер, элемент1, элемент2, ...]
                        
                        # Вычисляем требуемый размер памяти
                        required_size = 0x0100 + len(expected_data) + 1
                        if not self.processor.memory.ram or len(self.processor.memory.ram) < required_size:
                            new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                            while len(new_ram) < required_size:
                                new_ram.append(0)
                            self.processor.memory.ram = new_ram
                        
                        # Записываем данные постепенно: индекс показывает, сколько элементов уже записано
                        if self._task_data_write_index < len(expected_data):
                            new_ram = list(self.processor.memory.ram)
                            addr = 0x0100 + self._task_data_write_index
                            if addr < len(new_ram):
                                new_ram[addr] = int(expected_data[self._task_data_write_index]) & 0xFFFF
                                print(f"DEBUG execute_step: Записано значение {expected_data[self._task_data_write_index]} (0x{expected_data[self._task_data_write_index]:04X}) по адресу 0x{addr:04X} (элемент {self._task_data_write_index + 1}/{len(expected_data)})")
                                self.processor.memory.ram = new_ram
                                _update_history_ram(new_ram)
                                self._task_data_write_index += 1
                                print(f"DEBUG execute_step: Данные задачи 1: записан элемент {self._task_data_write_index}/{len(expected_data)}")
            
            elif self.current_task == 2:
                # Получаем данные задачи
                task = self.task_manager.get_task(2)
                if task:
                    test_data = task["test_data"]
                    if test_data and len(test_data) >= 2:
                        # Формат: [size_a, a1..aN, size_b, b1..bM]
                        size_a = test_data[0]
                        a_vals = test_data[1:1 + size_a]
                        size_b = test_data[1 + size_a]
                        b_vals = test_data[2 + size_a:2 + size_a + size_b]
                        
                        # Формируем последовательность данных для постепенной записи:
                        # [size_a, a1, a2, ..., aN, size_b, b1, b2, ..., bM]
                        task_data_sequence = [size_a] + a_vals + [size_b] + b_vals
                        total_elements = len(task_data_sequence)
                        
                        # Вычисляем требуемый размер памяти
                        required_size = max(0x020A, 0x030A) + 2
                        if not self.processor.memory.ram or len(self.processor.memory.ram) < required_size:
                            new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                            while len(new_ram) < required_size:
                                new_ram.append(0)
                            self.processor.memory.ram = new_ram
                        
                        # Записываем данные постепенно: один элемент за execute
                        if self._task_data_write_index < total_elements:
                            new_ram = list(self.processor.memory.ram)
                            
                            # Определяем адрес для записи
                            if self._task_data_write_index == 0:
                                # Первый элемент - размер массива A (0x0200)
                                addr = 0x0200
                            elif self._task_data_write_index <= size_a:
                                # Элементы массива A (0x0201 - 0x0200+size_a)
                                addr = 0x0200 + self._task_data_write_index
                            elif self._task_data_write_index == size_a + 1:
                                # Размер массива B (0x0300)
                                addr = 0x0300
                            else:
                                # Элементы массива B (0x0301 - 0x0300+size_b)
                                offset = self._task_data_write_index - (size_a + 2)  # -2 потому что size_a и size_b уже учтены
                                addr = 0x0300 + offset + 1
                            
                            if addr < len(new_ram):
                                value = task_data_sequence[self._task_data_write_index]
                                new_ram[addr] = int(value) & 0xFFFF
                                
                                # Определяем тип элемента для лога
                                if self._task_data_write_index == 0:
                                    elem_type = "размер массива A"
                                elif self._task_data_write_index <= size_a:
                                    elem_type = f"A[{self._task_data_write_index - 1}]"
                                elif self._task_data_write_index == size_a + 1:
                                    elem_type = "размер массива B"
                                else:
                                    elem_type = f"B[{self._task_data_write_index - size_a - 2}]"
                                
                                print(f"DEBUG execute_step: Записано значение {value} (0x{value:04X}) по адресу 0x{addr:04X} ({elem_type}, элемент {self._task_data_write_index + 1}/{total_elements})")
                                self.processor.memory.ram = new_ram
                                _update_history_ram(new_ram)
                                self._task_data_write_index += 1
                                print(f"DEBUG execute_step: Данные задачи 2: записан элемент {self._task_data_write_index}/{total_elements}")
            
            return {
                "success": True,
                "state": self.get_state(),
                "continues": continues,
                "message": "Step executed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Execution error: {str(e)}"
            }
    
    def execute_program(self, source_code: str = None, max_steps: int = 1000) -> Dict[str, Any]:
        """Выполнение всей программы"""
        try:
            if source_code:
                self.load_program(source_code)
            
            steps = 0
            while steps < max_steps and not self.processor.processor.is_halted:
                self.processor.step()
                steps += 1
            
            return {
                "success": True,
                "state": self.get_state(),
                "steps_executed": steps,
                "message": f"Program executed in {steps} steps"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Execution error: {str(e)}"
            }
    
    def get_state(self) -> Dict[str, Any]:
        """Получение текущего состояния эмулятора"""
        return self.processor.get_state()
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Получение списка задач"""
        return self.task_manager.get_all_tasks()
    
    def verify_current_task(self) -> Dict[str, Any]:
        """Проверка результата текущей задачи"""
        if not self.current_task:
            return {
                "success": False,
                "error": "No task loaded",
                "message": "No task is currently loaded"
            }
        
        try:
            result = self.task_manager.verify_task_result(self.processor, self.current_task)
            return {
                "success": True,
                "verification": result,
                "message": f"Task {self.current_task} verification completed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Verification error: {str(e)}"
            }
    
    def get_instruction_info(self, instruction: str) -> Dict[str, Any]:
        """Получение информации об инструкции"""
        return self.assembler.get_instruction_info(instruction)
    
    def disassemble_code(self, machine_code: List[str]) -> str:
        """Дизассемблирование машинного кода"""
        return self.assembler.disassemble(machine_code)