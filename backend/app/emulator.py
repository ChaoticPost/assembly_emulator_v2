"""
Эмулятор двухадресного RISC процессора с архитектурой Фон-Неймана
"""
from typing import List, Dict, Optional, Any
from .processor import RISCProcessor
from .assembler import RISCAssembler
from .tasks import TaskManager
from .models import EmulatorState, ProcessorState, MemoryState

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
            # Сбрасываем процессор
            self.reset()
            
            # Загружаем программу задачи
            self.load_program(task["program"])
            
            # Настраиваем данные задачи
            self.task_manager.setup_task_data(self.processor, task_id)
            
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