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
    if not emulator:
        raise HTTPException(status_code=500, detail="Emulator not initialized")
    
    try:
        result = emulator.compile_code(request.source_code)
        if result["success"]:
            # Загружаем программу в эмулятор для пошагового выполнения
            emulator.load_program(request.source_code)
        
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
        result = emulator.execute_step()
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