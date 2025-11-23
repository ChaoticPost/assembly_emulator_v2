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

    def reset(self):
        """Сброс эмулятора в начальное состояние"""
        self.processor.reset()
        self.current_task = None
    
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
            self.processor.processor.registers = [0] * 8
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
            
            # Восстанавливаем память после load_program (на всякий случай)
            if ram_before_load_program and len(ram_before_load_program) > 0:
                self.processor.memory.ram = ram_before_load_program
                print(f"DEBUG load_task: Память восстановлена после load_program, length={len(self.processor.memory.ram)}")
            
            # Настраиваем данные задачи (ВАЖНО: после load_program, чтобы память не сбросилась)
            self.task_manager.setup_task_data(self.processor, task_id)
            
            # КРИТИЧНО: Принудительно проверяем и исправляем данные для задачи 1
            if task_id == 1:
                # Проверяем все элементы массива
                expected_data = [7, 10, 20, 30, 40, 50, 60, 70]
                needs_fix = False
                
                # Проверяем размер памяти
                required_size = 0x0108  # До 0x0107 включительно
                if len(self.processor.memory.ram) < required_size:
                    print(f"DEBUG load_task: Расширяем память до {required_size}")
                    new_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                    while len(new_ram) < required_size:
                        new_ram.append(0)
                    self.processor.memory.ram = new_ram
                
                # Проверяем каждое значение
                for i, expected_val in enumerate(expected_data):
                    addr = 0x0100 + i
                    if addr < len(self.processor.memory.ram):
                        actual_val = self.processor.memory.ram[addr]
                        if actual_val != expected_val:
                            print(f"DEBUG load_task: ОШИБКА на адресе 0x{addr:04X}: ожидалось {expected_val}, получено {actual_val}")
                            needs_fix = True
                        else:
                            print(f"DEBUG load_task: OK на адресе 0x{addr:04X}: {actual_val} (0x{actual_val:04X}) ✓")
                    else:
                        print(f"DEBUG load_task: ОШИБКА: адрес 0x{addr:04X} вне границ памяти!")
                        needs_fix = True
                
                # Принудительно исправляем, если нужно
                if needs_fix:
                    print(f"DEBUG load_task: Принудительно исправляем память для задачи 1")
                    fixed_ram = list(self.processor.memory.ram) if self.processor.memory.ram else [0] * required_size
                    while len(fixed_ram) < required_size:
                        fixed_ram.append(0)
                    for i, expected_val in enumerate(expected_data):
                        addr = 0x0100 + i
                        fixed_ram[addr] = int(expected_val) & 0xFFFF
                        print(f"DEBUG load_task: Установлено fixed_ram[0x{addr:04X}] = {expected_val} (0x{expected_val:04X})")
                    # Создаем новый объект MemoryState для Pydantic
                    from .models import MemoryState
                    self.processor.memory = MemoryState(ram=fixed_ram, history=self.processor.memory.history)
                    print(f"DEBUG load_task: Память исправлена, проверка: memory.ram[0x0100]={self.processor.memory.ram[0x0100]}, memory.ram[0x0107]={self.processor.memory.ram[0x0107]}")
                else:
                    print(f"DEBUG load_task: Все данные задачи 1 корректны ✓")
            
            self.current_task = task_id
            
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
            
            continues = self.processor.step()
            
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