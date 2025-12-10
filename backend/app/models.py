from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class FlagType(str, Enum):
    ZERO = "zero"
    CARRY = "carry"
    OVERFLOW = "overflow"
    NEGATIVE = "negative"

class AddressingMode(str, Enum):
    IMMEDIATE = "immediate"      # Непосредственная адресация
    DIRECT = "direct"           # Прямая адресация
    REGISTER = "register"       # Регистровая адресация
    INDIRECT_REGISTER = "indirect_register"  # Косвенно-регистровая адресация

class ProcessorState(BaseModel):
    """Состояние процессора для одноадресной архитектуры Фон-Неймана"""
    # Аккумулятор - единственный регистр для операций
    accumulator: int = 0  # ACC - аккумулятор
    
    # Специальные регистры
    program_counter: int = 0        # PC - счетчик команд
    instruction_register: int = 0   # IR - регистр команд
    instruction_register_asm: str = ""  # Ассемблерное представление команды
    
    # Флаги процессора
    flags: Dict[str, bool] = {
        "zero": False,      # Z - флаг нуля
        "carry": False,     # C - флаг переноса
        "overflow": False,  # V - флаг переполнения
        "negative": False   # N - флаг знака
    }
    
    # Состояние выполнения
    current_command: str = ""
    is_halted: bool = False
    cycles: int = 0

class MemoryState(BaseModel):
    """Состояние памяти"""
    ram: List[int] = []
    history: List[Dict[str, Any]] = []

class EmulatorState(BaseModel):
    """Общее состояние эмулятора"""
    processor: ProcessorState
    memory: MemoryState
    source_code: str = ""
    machine_code: List[str] = []
    current_task: Optional[int] = None

class TaskInfo(BaseModel):
    """Информация о задаче"""
    id: int
    title: str
    description: str

class CompileRequest(BaseModel):
    """Запрос на компиляцию кода"""
    source_code: str
    task_id: Optional[int] = None  # ID задачи для автоматической загрузки данных

class LoadTaskRequest(BaseModel):
    """Запрос на загрузку данных задачи"""
    task_id: int

class ExecuteRequest(BaseModel):
    """Запрос на выполнение"""
    task_id: Optional[int] = None
    step_by_step: bool = False
    source_code: Optional[str] = None

class ResetRequest(BaseModel):
    """Запрос на сброс"""
    pass

class TaskData(BaseModel):
    """Данные для задачи"""
    array_a: List[int]
    array_b: Optional[List[int]] = None
    result_address: int = 0x1100

class InstructionField(BaseModel):
    """Поля команды для отображения (одноадресная архитектура)"""
    opcode: int
    opcode_bits: str
    operand: int = 0     # Операнд (адрес или значение)
    operand_bits: str = ""
    immediate: int = 0   # Непосредственное значение
    immediate_bits: str = ""
    addressing_mode: AddressingMode = AddressingMode.REGISTER
    instruction_type: str = ""  # Тип команды (I, J, S)
