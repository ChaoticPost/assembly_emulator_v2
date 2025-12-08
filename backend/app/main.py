"""
FastAPI приложение для эмулятора двухадресного RISC процессора
"""
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from .models import (
    EmulatorState, CompileRequest, LoadTaskRequest, ExecuteRequest, ResetRequest, 
    TaskInfo, TaskData
)
from .emulator import RISCEmulator

# Глобальный объект эмулятора
emulator = None

def has_manual_array_initialization(source_code: str, task_id: int = None) -> bool:
    """
    Определяет, содержит ли исходный код ручную инициализацию массива(ов).
    
    Для задачи 1 проверяет наличие команд STR для записи:
    - Размера массива по адресу 0x0100 (или 256 в десятичной)
    - Элементов массива по адресам 0x0101-0x010F (или 257-271 в десятичной)
    
    Для задачи 2 проверяет наличие команд STR для записи:
    - Размера массива A по адресу 0x0200 (или 512 в десятичной)
    - Элементов массива A по адресам 0x0201-0x020A (или 513-522 в десятичной)
    - Размера массива B по адресу 0x0300 (или 768 в десятичной)
    - Элементов массива B по адресам 0x0301-0x030A (или 769-778 в десятичной)
    
    Args:
        source_code: Исходный код на ассемблере
        task_id: ID задачи (1 или 2) для определения типа проверки
        
    Returns:
        True, если код содержит ручную инициализацию массива(ов)
    """
    if not source_code:
        return False
    
    # Нормализуем код: убираем комментарии, приводим к верхнему регистру
    lines = source_code.split('\n')
    normalized_lines = []
    for line in lines:
        # Убираем комментарии
        if ';' in line:
            line = line[:line.index(';')]
        line = line.strip()
        if line:
            normalized_lines.append(line)
    
    # Проверяем каждую строку на наличие STR команд с нужными адресами
    if task_id == 1:
        # Проверка для задачи 1
        has_size_init = False
        has_element_init = False
        
        for line in normalized_lines:
            line_upper = line.upper()
            # Пропускаем строки без STR
            if 'STR' not in line_upper:
                continue
            
            # Извлекаем адрес из строки вида "STR R7, [0x0100]" или "STR R7, [256]"
            address_match = re.search(r'STR\s+R\d+\s*,\s*\[([^\]]+)\]', line_upper)
            if address_match:
                address_str = address_match.group(1).strip()
                
                # Парсим адрес (может быть hex или decimal)
                try:
                    if address_str.startswith('0X'):
                        address = int(address_str, 16)
                    else:
                        address = int(address_str)
                    
                    # Проверяем адрес размера массива (0x0100 = 256)
                    if address == 0x0100 or address == 256:
                        has_size_init = True
                        print(f"DEBUG has_manual_array_initialization (task 1): Найдена запись размера: {line.strip()}")
                    
                    # Проверяем адреса элементов массива (0x0101-0x010F = 257-271)
                    if (0x0101 <= address <= 0x010F) or (257 <= address <= 271):
                        has_element_init = True
                        print(f"DEBUG has_manual_array_initialization (task 1): Найдена запись элемента: {line.strip()}, адрес=0x{address:04X}")
                except ValueError:
                    # Не удалось распарсить адрес, пропускаем
                    continue
        
        # Если найдена запись размера И хотя бы одного элемента - это ручная инициализация
        result = has_size_init and has_element_init
        print(f"DEBUG has_manual_array_initialization (task 1): has_size_init={has_size_init}, has_element_init={has_element_init}, result={result}")
        return result
    
    elif task_id == 2:
        # Проверка для задачи 2
        has_size_a_init = False
        has_element_a_init = False
        has_size_b_init = False
        has_element_b_init = False
        
        for line in normalized_lines:
            line_upper = line.upper()
            # Пропускаем строки без STR
            if 'STR' not in line_upper:
                continue
            
            # Извлекаем адрес из строки вида "STR R7, [0x0200]" или "STR R7, [512]"
            address_match = re.search(r'STR\s+R\d+\s*,\s*\[([^\]]+)\]', line_upper)
            if address_match:
                address_str = address_match.group(1).strip()
                
                # Парсим адрес (может быть hex или decimal)
                try:
                    if address_str.startswith('0X'):
                        address = int(address_str, 16)
                    else:
                        address = int(address_str)
                    
                    # Проверяем адрес размера массива A (0x0200 = 512)
                    if address == 0x0200 or address == 512:
                        has_size_a_init = True
                        print(f"DEBUG has_manual_array_initialization (task 2): Найдена запись размера массива A: {line.strip()}")
                    
                    # Проверяем адреса элементов массива A (0x0201-0x020A = 513-522)
                    if (0x0201 <= address <= 0x020A) or (513 <= address <= 522):
                        has_element_a_init = True
                        print(f"DEBUG has_manual_array_initialization (task 2): Найдена запись элемента массива A: {line.strip()}, адрес=0x{address:04X}")
                    
                    # Проверяем адрес размера массива B (0x0300 = 768)
                    if address == 0x0300 or address == 768:
                        has_size_b_init = True
                        print(f"DEBUG has_manual_array_initialization (task 2): Найдена запись размера массива B: {line.strip()}")
                    
                    # Проверяем адреса элементов массива B (0x0301-0x030A = 769-778)
                    if (0x0301 <= address <= 0x030A) or (769 <= address <= 778):
                        has_element_b_init = True
                        print(f"DEBUG has_manual_array_initialization (task 2): Найдена запись элемента массива B: {line.strip()}, адрес=0x{address:04X}")
                except ValueError:
                    # Не удалось распарсить адрес, пропускаем
                    continue
        
        # Если найдена запись размера и элементов для обоих массивов - это ручная инициализация
        result = (has_size_a_init and has_element_a_init) and (has_size_b_init and has_element_b_init)
        print(f"DEBUG has_manual_array_initialization (task 2): has_size_a={has_size_a_init}, has_element_a={has_element_a_init}, has_size_b={has_size_b_init}, has_element_b={has_element_b_init}, result={result}")
        return result
    
    else:
        # Если task_id не указан, проверяем оба варианта
        # Проверка для задачи 1
        has_task1 = has_manual_array_initialization(source_code, task_id=1)
        # Проверка для задачи 2
        has_task2 = has_manual_array_initialization(source_code, task_id=2)
        return has_task1 or has_task2

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения"""
    global emulator
    
    emulator = RISCEmulator()
    
    yield
    
    # Очистка при завершении
    emulator = None

app = FastAPI(
    title="Эмулятор двухадресного RISC процессора",
    description="Backend для эмулятора двухадресного RISC процессора с архитектурой Фон-Неймана",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Эмулятор двухадресного RISC процессора API"}

@app.get("/api/state", response_model=EmulatorState)
async def get_state():
    """Получить текущее состояние эмулятора"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    state = emulator.get_state()
    return EmulatorState(**state)

@app.post("/api/compile")
async def compile_code(request: CompileRequest):
    """Скомпилировать исходный код"""
    # КРИТИЧНО: Логируем СРАЗУ при получении запроса (и в stdout, и в stderr)
    import sys
    log_msg = f"DEBUG compile: ===== ЗАПРОС ПОЛУЧЕН ===== task_id={request.task_id}, source_code length={len(request.source_code) if request.source_code else 0}"
    print(log_msg, file=sys.stderr, flush=True)
    print(log_msg, flush=True)
    
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    try:
        # Проверяем, содержит ли код ручную инициализацию массива(ов)
        # Передаем task_id для правильной проверки
        has_manual_init = has_manual_array_initialization(request.source_code, task_id=request.task_id)
        print(f"DEBUG compile: has_manual_array_initialization (task_id={request.task_id})={has_manual_init}")
        
        # Если указан task_id, загружаем данные задачи ПЕРЕД компиляцией
        # НО только если код НЕ содержит ручную инициализацию
        if request.task_id and not has_manual_init:
            print(f"DEBUG compile: Загружаем данные задачи {request.task_id} перед компиляцией (нет ручной инициализации)")
            # Сохраняем текущую память (если есть)
            ram_before_task = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            print(f"DEBUG compile: Память ДО load_task: length={len(ram_before_task)}, ram[0x0100]={ram_before_task[0x0100] if 0x0100 < len(ram_before_task) else 'OUT_OF_BOUNDS'}")
            
            task_result = emulator.load_task(request.task_id)
            if task_result["success"]:
                print(f"DEBUG compile: Данные задачи {request.task_id} загружены")
                print(f"DEBUG compile: memory.ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                print(f"DEBUG compile: memory.ram.length={len(emulator.processor.memory.ram)}")
                
                # КРИТИЧНО: Проверяем, что данные действительно загружены
                if 0x0100 < len(emulator.processor.memory.ram):
                    check_val = emulator.processor.memory.ram[0x0100]
                    if check_val == 0:
                        print(f"ERROR compile: Данные задачи НЕ загружены! ram[0x0100]={check_val}, ожидалось 7")
                    else:
                        print(f"OK compile: Данные задачи загружены успешно, ram[0x0100]={check_val}")
            else:
                print(f"WARNING compile: Не удалось загрузить данные задачи {request.task_id}: {task_result.get('error')}")
        elif request.task_id and has_manual_init:
            print(f"DEBUG compile: task_id={request.task_id} указан, но код содержит ручную инициализацию массива - пропускаем загрузку данных задачи")
        else:
            print(f"DEBUG compile: task_id не указан, пропускаем загрузку данных задачи")
        
        # Сохраняем память ПОСЛЕ load_task (чтобы не потерять данные задачи)
        # Но только если данные задачи были загружены (нет ручной инициализации)
        saved_ram = None
        saved_ram_size = 0
        if request.task_id and not has_manual_init:
            # Сохраняем память ПОСЛЕ load_task, которая содержит данные задачи
            saved_ram = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            saved_ram_size = len(saved_ram) if saved_ram else emulator.processor.memory_size
            print(f"DEBUG compile START: memory_size={saved_ram_size}, ram[0x0100]={saved_ram[0x0100] if saved_ram and 0x0100 < len(saved_ram) else 'OUT_OF_BOUNDS'}")
            # Проверяем, что данные задачи действительно в памяти
            if saved_ram and 0x0100 < len(saved_ram):
                check_val = saved_ram[0x0100]
                print(f"DEBUG compile START: Проверка saved_ram[0x0100]={check_val} (0x{check_val:04X})")
                if check_val == 0:
                    print(f"WARNING compile START: saved_ram[0x0100] = 0, данные задачи могут быть не загружены!")
        else:
            # Если есть ручная инициализация, ОЧИЩАЕМ память, чтобы пользователь мог записать свои данные
            # ВАЖНО: Инициализируем память нулями, чтобы STR команды могли записывать данные
            min_size = max(0x0200, emulator.processor.memory_size)  # Минимум до 0x0200 для задачи 1
            emulator.processor.memory.ram = [0] * min_size
            print(f"DEBUG compile START: Ручная инициализация, память очищена и инициализирована размером {min_size}")
            saved_ram = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            saved_ram_size = len(saved_ram) if saved_ram else emulator.processor.memory_size
            print(f"DEBUG compile START: Ручная инициализация, память очищена, size={saved_ram_size}, ram[0x0100]={saved_ram[0x0100] if saved_ram and 0x0100 < len(saved_ram) else 'OUT_OF_BOUNDS'}")
        
        result = emulator.compile_code(request.source_code)
        if result["success"]:
            # Сохраняем память перед load_program
            ram_before_load = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            
            # Сохраняем память ПЕРЕД load_program
            ram_before_load_program = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            if request.task_id == 1:
                print(f"DEBUG compile: Память ПЕРЕД load_program: length={len(ram_before_load_program)}, ram[0x0100]={ram_before_load_program[0x0100] if ram_before_load_program and 0x0100 < len(ram_before_load_program) else 'OUT_OF_BOUNDS'}")
            elif request.task_id == 2:
                print(f"DEBUG compile: Память ПЕРЕД load_program: length={len(ram_before_load_program)}, ram[0x0200]={ram_before_load_program[0x0200] if ram_before_load_program and 0x0200 < len(ram_before_load_program) else 'OUT_OF_BOUNDS'}, ram[0x0300]={ram_before_load_program[0x0300] if ram_before_load_program and 0x0300 < len(ram_before_load_program) else 'OUT_OF_BOUNDS'}")
            else:
                print(f"DEBUG compile: Память ПЕРЕД load_program: length={len(ram_before_load_program)}")
            
            # Загружаем программу в эмулятор для пошагового выполнения
            # ВАЖНО: load_program НЕ сбрасывает память, только регистры и историю
            emulator.load_program(request.source_code)
            
            # Проверяем память ПОСЛЕ load_program
            ram_after_load_program = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            if request.task_id == 1:
                print(f"DEBUG compile: Память ПОСЛЕ load_program: length={len(ram_after_load_program)}, ram[0x0100]={ram_after_load_program[0x0100] if ram_after_load_program and 0x0100 < len(ram_after_load_program) else 'OUT_OF_BOUNDS'}")
            elif request.task_id == 2:
                print(f"DEBUG compile: Память ПОСЛЕ load_program: length={len(ram_after_load_program)}, ram[0x0200]={ram_after_load_program[0x0200] if ram_after_load_program and 0x0200 < len(ram_after_load_program) else 'OUT_OF_BOUNDS'}, ram[0x0300]={ram_after_load_program[0x0300] if ram_after_load_program and 0x0300 < len(ram_after_load_program) else 'OUT_OF_BOUNDS'}")
            else:
                print(f"DEBUG compile: Память ПОСЛЕ load_program: length={len(ram_after_load_program)}")
            
            # Восстанавливаем память
            # Если была загружена задача (нет ручной инициализации) - восстанавливаем данные задачи
            # Если есть ручная инициализация - НЕ восстанавливаем, чтобы пользователь мог сам записать данные
            if request.task_id and not has_manual_init:
                # Используем saved_ram, которая содержит данные задачи (сохранена ПОСЛЕ load_task)
                if saved_ram and len(saved_ram) > 0:
                    # Гарантируем достаточный размер
                    if len(saved_ram) < saved_ram_size:
                        saved_ram.extend([0] * (saved_ram_size - len(saved_ram)))
                    emulator.processor.memory.ram = list(saved_ram)  # Создаем новый список для Pydantic
                    print(f"DEBUG compile: Memory restored from saved_ram (with task data), size={len(emulator.processor.memory.ram)}")
                    # Проверяем, что данные задачи действительно восстановлены
                    if request.task_id == 1:
                        print(f"DEBUG compile: Проверка памяти для задачи 1: ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                        if 0x0100 < len(emulator.processor.memory.ram):
                            check_val = emulator.processor.memory.ram[0x0100]
                            print(f"DEBUG compile: Проверка восстановленной памяти ram[0x0100]={check_val} (0x{check_val:04X})")
                            if check_val == 0:
                                print(f"ERROR compile: Восстановленная память ram[0x0100] = 0, данные задачи потеряны!")
                                # Пытаемся использовать ram_before_load_program как резерв
                                if ram_before_load_program and len(ram_before_load_program) > 0 and 0x0100 < len(ram_before_load_program):
                                    backup_val = ram_before_load_program[0x0100]
                                    if backup_val != 0:
                                        print(f"DEBUG compile: Используем резервную память ram_before_load_program, ram[0x0100]={backup_val}")
                                        emulator.processor.memory.ram = list(ram_before_load_program)
                    elif request.task_id == 2:
                        print(f"DEBUG compile: Проверка памяти для задачи 2: ram[0x0200]={emulator.processor.memory.ram[0x0200] if 0x0200 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}, ram[0x0300]={emulator.processor.memory.ram[0x0300] if 0x0300 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                        if 0x0200 < len(emulator.processor.memory.ram) and 0x0300 < len(emulator.processor.memory.ram):
                            check_val_a = emulator.processor.memory.ram[0x0200]
                            check_val_b = emulator.processor.memory.ram[0x0300]
                            print(f"DEBUG compile: Проверка восстановленной памяти ram[0x0200]={check_val_a} (0x{check_val_a:04X}), ram[0x0300]={check_val_b} (0x{check_val_b:04X})")
                            if check_val_a == 0 or check_val_b == 0:
                                print(f"ERROR compile: Восстановленная память ram[0x0200]={check_val_a} или ram[0x0300]={check_val_b} = 0, данные задачи потеряны!")
                                # Пытаемся использовать ram_before_load_program как резерв
                                if ram_before_load_program and len(ram_before_load_program) > 0:
                                    if 0x0200 < len(ram_before_load_program) and 0x0300 < len(ram_before_load_program):
                                        backup_val_a = ram_before_load_program[0x0200]
                                        backup_val_b = ram_before_load_program[0x0300]
                                        if backup_val_a != 0 and backup_val_b != 0:
                                            print(f"DEBUG compile: Используем резервную память ram_before_load_program, ram[0x0200]={backup_val_a}, ram[0x0300]={backup_val_b}")
                                            emulator.processor.memory.ram = list(ram_before_load_program)
                elif ram_before_load_program and len(ram_before_load_program) > 0:
                    # Если saved_ram пустая, используем ram_before_load_program
                    emulator.processor.memory.ram = list(ram_before_load_program)
                    print(f"DEBUG compile: Memory restored from ram_before_load_program (saved_ram was empty), size={len(emulator.processor.memory.ram)}, ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                else:
                    print(f"WARNING compile: No RAM to restore for task {request.task_id}!")
            elif has_manual_init:
                # Если есть ручная инициализация, восстанавливаем ОЧИЩЕННУЮ память из saved_ram (нули)
                # Пользователь сам запишет данные через STR команды при выполнении
                if saved_ram and len(saved_ram) > 0:
                    # Используем saved_ram, которая содержит очищенную память (нули)
                    if len(saved_ram) < saved_ram_size:
                        saved_ram.extend([0] * (saved_ram_size - len(saved_ram)))
                    emulator.processor.memory.ram = list(saved_ram)  # Создаем новый список для Pydantic
                    print(f"DEBUG compile: Ручная инициализация - восстановлена очищенная память, size={len(emulator.processor.memory.ram)}, ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                else:
                    # Если saved_ram пустая, создаем новую очищенную память
                    min_size = max(0x0200, emulator.processor.memory_size)
                    emulator.processor.memory.ram = [0] * min_size
                    print(f"DEBUG compile: Ручная инициализация - создана новая очищенная память, size={min_size}")
            else:
                # Если нет task_id, используем текущую память или ram_before_load_program
                if ram_before_load_program and len(ram_before_load_program) > 0:
                    emulator.processor.memory.ram = list(ram_before_load_program)
                    print(f"DEBUG compile: Memory restored from ram_before_load_program, size={len(emulator.processor.memory.ram)}, ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
                else:
                    print(f"WARNING compile: No RAM to restore!")
        
        # Возвращаем результат с текущим состоянием (включая память)
        if result["success"]:
            state = emulator.get_state()
            result["state"] = state
            print(f"DEBUG compile: Returning state with memory.ram[0x0100]={state['memory']['ram'][0x0100] if 0x0100 < len(state['memory']['ram']) else 'OUT_OF_BOUNDS'}")
            # Проверяем все элементы массива для задачи 1
            if request.task_id == 1:
                print(f"DEBUG compile: Проверка памяти для задачи 1:")
                for addr in [0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107]:
                    if addr < len(state['memory']['ram']):
                        val = state['memory']['ram'][addr]
                        print(f"  memory.ram[0x{addr:04X}] = {val} (0x{val:04X})")
                    else:
                        print(f"  memory.ram[0x{addr:04X}] = OUT_OF_BOUNDS")
            # Проверяем все элементы массивов для задачи 2
            elif request.task_id == 2:
                print(f"DEBUG compile: Проверка памяти для задачи 2:")
                print(f"  Массив A:")
                for addr in [0x0200, 0x0201, 0x0202, 0x0203, 0x0204, 0x0205]:
                    if addr < len(state['memory']['ram']):
                        val = state['memory']['ram'][addr]
                        print(f"    memory.ram[0x{addr:04X}] = {val} (0x{val:04X})")
                    else:
                        print(f"    memory.ram[0x{addr:04X}] = OUT_OF_BOUNDS")
                print(f"  Массив B:")
                for addr in [0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0305]:
                    if addr < len(state['memory']['ram']):
                        val = state['memory']['ram'][addr]
                        print(f"    memory.ram[0x{addr:04X}] = {val} (0x{val:04X})")
                    else:
                        print(f"    memory.ram[0x{addr:04X}] = OUT_OF_BOUNDS")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка компиляции: {str(e)}")

@app.post("/api/load-task")
async def load_task(request: LoadTaskRequest):
    """Загрузить данные задачи без выполнения программы"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    try:
        result = emulator.load_task(request.task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка загрузки задачи: {str(e)}")

@app.post("/api/execute")
async def execute_code(request: ExecuteRequest):
    """Выполнить код"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    try:
        if request.task_id and request.task_id > 0:
            # Выполнение предустановленной задачи
            result = emulator.load_task(request.task_id)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            
            # Выполняем программу
            execute_result = emulator.execute_program(max_steps=1000)
            
            # Проверяем результат
            verification = emulator.verify_current_task()
            
            return {
                "success": True,
                "task_id": request.task_id,
                "verification": verification.get("verification"),
                "state": execute_result["state"]
            }
        else:
            # Выполнение пользовательского кода
            if not request.source_code:
                raise HTTPException(status_code=400, detail="Не указан исходный код для выполнения")
            
            result = emulator.execute_program(request.source_code)
            return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка выполнения: {str(e)}")

@app.post("/api/step")
async def execute_step():
    """Выполнить один шаг"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    try:
        # Сохраняем память ПЕРЕД выполнением шага (чтобы не потерять данные)
        ram_before_step = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
        
        # Проверяем память перед выполнением шага
        if ram_before_step and 0x0100 < len(ram_before_step):
            mem_val = ram_before_step[0x0100]
            print(f"DEBUG step endpoint: Память ПЕРЕД шагом, ram[0x0100]={mem_val} (0x{mem_val:04X}), size={len(ram_before_step)}")
        else:
            print(f"DEBUG step endpoint: Память слишком мала или пустая! length={len(ram_before_step)}")
            # Инициализируем память, если она пустая
            if not ram_before_step or len(ram_before_step) == 0:
                min_size = max(0x0200, emulator.processor.memory_size)
                emulator.processor.memory.ram = [0] * min_size
                ram_before_step = list(emulator.processor.memory.ram)
                print(f"DEBUG step endpoint: Инициализирована память размером {min_size}")
        
        # Получаем текущую фазу выполнения (если есть последняя запись в истории)
        last_history_entry = None
        if emulator.processor.memory.history and len(emulator.processor.memory.history) > 0:
            last_history_entry = emulator.processor.memory.history[-1]
        
        # Выполняем шаг
        result = emulator.execute_step()
        
        # Получаем информацию о выполненной фазе из последней записи истории
        phase_info = None
        if result.get("state") and result["state"].get("memory"):
            history = result["state"]["memory"].get("history", [])
            if history and len(history) > 0:
                last_entry = history[-1]
                phase_info = last_entry.get("execution_phase")
                command_info = last_entry.get("command", "-")
                if phase_info:
                    phase_display = phase_info.upper()
                    print(f"═══════════════════════════════════════════════════════════════")
                    print(f"🔹 ФАЗА ВЫПОЛНЕНИЯ: {phase_display} | Команда: {command_info}")
                    print(f"═══════════════════════════════════════════════════════════════")
        
        # Проверяем память после выполнения шага
        ram_after_step = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
        if ram_after_step and 0x0100 < len(ram_after_step):
            mem_val = ram_after_step[0x0100]
            print(f"DEBUG step endpoint: Память ПОСЛЕ шага, ram[0x0100]={mem_val} (0x{mem_val:04X}), size={len(ram_after_step)}")
            
            # Проверяем, что память не потерялась
            if len(ram_after_step) < len(ram_before_step):
                print(f"WARNING step endpoint: Память уменьшилась! Было {len(ram_before_step)}, стало {len(ram_after_step)}")
                # Восстанавливаем память из резервной копии
                emulator.processor.memory.ram = list(ram_before_step)
                print(f"DEBUG step endpoint: Память восстановлена из резервной копии")
                ram_after_step = list(emulator.processor.memory.ram)
            
            # Проверяем все элементы массива для задачи 1 или для кода с ручной инициализацией
            # Проверяем адреса 0x0100-0x0107, которые используются для инициализации массива
            print(f"DEBUG step endpoint: Проверка памяти после шага (адреса 0x0100-0x0107):")
            for addr in [0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107]:
                if addr < len(ram_after_step):
                    val = ram_after_step[addr]
                    before_val = ram_before_step[addr] if ram_before_step and addr < len(ram_before_step) else 'N/A'
                    if val != before_val:
                        print(f"  memory.ram[0x{addr:04X}] = {val} (0x{val:04X}) [ИЗМЕНЕНО, было {before_val}]")
                    else:
                        print(f"  memory.ram[0x{addr:04X}] = {val} (0x{val:04X})")
                else:
                    print(f"  memory.ram[0x{addr:04X}] = OUT_OF_BOUNDS")
        
        # Проверяем состояние памяти в результате
        if result.get("state") and result["state"].get("memory"):
            state_mem = result["state"]["memory"]
            if state_mem.get("ram") and 0x0100 < len(state_mem["ram"]):
                state_val = state_mem["ram"][0x0100]
                print(f"DEBUG step endpoint: Память в состоянии результата, ram[0x0100]={state_val} (0x{state_val:04X})")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка выполнения шага: {str(e)}")

@app.post("/api/reset")
async def reset_processor():
    """Сбросить процессор"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    emulator.reset()
    return {
        "success": True,
        "message": "Процессор сброшен",
        "state": emulator.get_state()
    }

@app.get("/api/tasks", response_model=List[TaskInfo])
async def get_tasks():
    """Получить список задач"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    tasks = emulator.get_tasks()
    return [TaskInfo(**task) for task in tasks]

@app.get("/api/tasks/{task_id}", response_model=TaskInfo)
async def get_task(task_id: int):
    """Получить информацию о задаче"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    tasks = emulator.get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return TaskInfo(**task)

@app.get("/api/tasks/{task_id}/program")
async def get_task_program(task_id: int):
    """Получить программу задачи"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    tasks = emulator.get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return {
        "task_id": task_id,
        "program": task.get("program", ""),
        "test_data": task.get("test_data", [])
    }

@app.get("/api/instruction/{instruction}")
async def get_instruction_info(instruction: str):
    """Получить информацию об инструкции"""
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    return emulator.get_instruction_info(instruction)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)