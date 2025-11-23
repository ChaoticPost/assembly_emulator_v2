"""
FastAPI приложение для эмулятора двухадресного RISC процессора
"""
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
        
        # Если указан task_id, загружаем данные задачи ПЕРЕД компиляцией
        if request.task_id:
            print(f"DEBUG compile: Загружаем данные задачи {request.task_id} перед компиляцией")
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
        else:
            print(f"DEBUG compile: task_id не указан, пропускаем загрузку данных задачи")
        
        # Сохраняем память ПОСЛЕ load_task (чтобы не потерять данные задачи)
        saved_ram = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
        saved_ram_size = len(saved_ram) if saved_ram else emulator.processor.memory_size
        print(f"DEBUG compile START: memory_size={saved_ram_size}, ram[0x0100]={saved_ram[0x0100] if 0x0100 < len(saved_ram) else 'OUT_OF_BOUNDS'}")
        
        result = emulator.compile_code(request.source_code)
        if result["success"]:
            # Сохраняем память перед load_program
            ram_before_load = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            
            # Сохраняем память ПЕРЕД load_program (данные задачи)
            ram_before_load_program = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            print(f"DEBUG compile: Память ПЕРЕД load_program: length={len(ram_before_load_program)}, ram[0x0100]={ram_before_load_program[0x0100] if 0x0100 < len(ram_before_load_program) else 'OUT_OF_BOUNDS'}")
            
            # Загружаем программу в эмулятор для пошагового выполнения
            # ВАЖНО: load_program НЕ сбрасывает память, только регистры и историю
            emulator.load_program(request.source_code)
            
            # Проверяем память ПОСЛЕ load_program
            ram_after_load_program = list(emulator.processor.memory.ram) if emulator.processor.memory.ram else []
            print(f"DEBUG compile: Память ПОСЛЕ load_program: length={len(ram_after_load_program)}, ram[0x0100]={ram_after_load_program[0x0100] if 0x0100 < len(ram_after_load_program) else 'OUT_OF_BOUNDS'}")
            
            # Восстанавливаем память (данные задачи должны сохраниться)
            # ВАЖНО: используем saved_ram (память ПОСЛЕ load_task с данными задачи)
            # ram_before_load_program может быть пустой или не содержать данные задачи
            if saved_ram and len(saved_ram) > 0:
                # Используем saved_ram, которая содержит данные задачи
                if len(saved_ram) < saved_ram_size:
                    saved_ram.extend([0] * (saved_ram_size - len(saved_ram)))
                emulator.processor.memory.ram = list(saved_ram)  # Создаем новый список для Pydantic
                print(f"DEBUG compile: Memory restored from saved_ram (with task data), size={len(emulator.processor.memory.ram)}, ram[0x0100]={emulator.processor.memory.ram[0x0100] if 0x0100 < len(emulator.processor.memory.ram) else 'OUT_OF_BOUNDS'}")
            elif ram_before_load_program and len(ram_before_load_program) > 0:
                # Если saved_ram пустая, используем ram_before_load_program
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
        # Проверяем память перед выполнением шага
        if 0x0100 < len(emulator.processor.memory.ram):
            mem_val = emulator.processor.memory.ram[0x0100]
            print(f"DEBUG step endpoint: Память ПЕРЕД шагом, ram[0x0100]={mem_val} (0x{mem_val:04X})")
        else:
            print(f"DEBUG step endpoint: Память слишком мала! length={len(emulator.processor.memory.ram) if emulator.processor.memory.ram else 0}")
        
        result = emulator.execute_step()
        
        # Проверяем память после выполнения шага
        if 0x0100 < len(emulator.processor.memory.ram):
            mem_val = emulator.processor.memory.ram[0x0100]
            print(f"DEBUG step endpoint: Память ПОСЛЕ шага, ram[0x0100]={mem_val} (0x{mem_val:04X})")
            # Проверяем все элементы массива для задачи 1
            if emulator.current_task == 1:
                print(f"DEBUG step endpoint: Проверка памяти задачи 1 после шага:")
                for addr in [0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107]:
                    if addr < len(emulator.processor.memory.ram):
                        val = emulator.processor.memory.ram[addr]
                        print(f"  memory.ram[0x{addr:04X}] = {val} (0x{val:04X})")
        
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