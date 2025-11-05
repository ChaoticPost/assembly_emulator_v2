"""
Предустановленные задачи для эмулятора двухадресного RISC процессора
"""
from typing import List, Dict, Any
from .processor import RISCProcessor

class TaskManager:
    """Менеджер задач для эмулятора"""
    
    def __init__(self):
        self.tasks = {
            1: {
                "id": 1,
                "title": "Сумма элементов массива",
                "description": "Вычислить сумму всех элементов массива из 6-15 элементов. Использовать цикл для итерации по элементам. Чтение из памяти в регистры.",
                "program": self._get_sum_array_program(),
                "test_data": self._generate_sum_test_data()
            },
            2: {
                "id": 2,
                "title": "Свертка двух массивов",
                "description": "Вычислить свертку двух массивов по 10 элементов каждый. Результат сохранить в память по адресу 0x1100.",
                "program": self._get_convolution_program(),
                "test_data": self._generate_convolution_test_data()
            }
        }
    
    def get_task(self, task_id: int) -> Dict[str, Any]:
        """Получить информацию о задаче"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Получить все задачи"""
        return list(self.tasks.values())
    
    def _get_sum_array_program(self) -> str:
        """Программа для суммы элементов массива"""
        return """
; Программа для вычисления суммы элементов массива
; Формат массива: [размер, элемент1, элемент2, ..., элементN]
; Массив: [7, 10, 20, 30, 40, 50, 60, 70] (размер=7, элементы: 10-70)
; Ожидаемый результат: 280

; Инициализация
LDI R0, 0          ; R0 = 0 (аккумулятор для суммы)
LDI R1, 1          ; R1 = 1 (индекс, начинается с 1, так как [0] - размер)
LDI R2, 0x1000     ; R2 = базовый адрес массива

; Загрузка размера массива
LDR R3, [0x1000]   ; R3 = размер массива (из [0x1000])

; Основной цикл
LOOP_START:
; Сравниваем индекс с (размер + 1)
; Если индекс == размер + 1, значит обработали все элементы, выходим
ADD R4, R3, 1      ; R4 = размер + 1
CMP R1, R4         ; Сравнить индекс с (размер + 1)
JZ LOOP_END        ; Если индекс == размер + 1, выйти из цикла

; Вычисляем адрес текущего элемента: базовый_адрес + индекс
ADD R5, R2, R1     ; R5 = 0x1000 + индекс (адрес элемента)
LDRR R6, [R5]      ; R6 = [R5] (значение элемента массива)

; Добавляем элемент к сумме
ADD R0, R0, R6     ; R0 = R0 + R6 (сумма)

; Увеличиваем индекс
ADD R1, R1, 1      ; R1 = R1 + 1

JMP LOOP_START     ; Переход к началу цикла

LOOP_END:
; Результат в R0 (аккумулятор)
HALT
        """.strip()
    
    def _get_convolution_program(self) -> str:
        """Программа для свертки двух массивов"""
        return """
; Программа для вычисления свертки двух массивов
; Массив A: [2, 3, 1, 4, 5, 2, 3, 1, 4, 2] (10 элементов)
; Массив B: [1, 2, 3, 1, 2, 3, 1, 2, 3, 1] (10 элементов)
; Результат: скалярное произведение = 50

; Инициализация
LDI R0, 0          ; R0 = 0 (аккумулятор)
LDI R1, 0          ; R1 = 0 (индекс)

; Загрузка массива A в память (адреса 0x1000-0x1009)
LDI R2, 2
STR R2, [0x1000]
LDI R2, 3
STR R2, [0x1001]
LDI R2, 1
STR R2, [0x1002]
LDI R2, 4
STR R2, [0x1003]
LDI R2, 5
STR R2, [0x1004]
LDI R2, 2
STR R2, [0x1005]
LDI R2, 3
STR R2, [0x1006]
LDI R2, 1
STR R2, [0x1007]
LDI R2, 4
STR R2, [0x1008]
LDI R2, 2
STR R2, [0x1009]

; Загрузка массива B в память (адреса 0x1010-0x1019)
LDI R2, 1
STR R2, [0x1010]
LDI R2, 2
STR R2, [0x1011]
LDI R2, 3
STR R2, [0x1012]
LDI R2, 1
STR R2, [0x1013]
LDI R2, 2
STR R2, [0x1014]
LDI R2, 3
STR R2, [0x1015]
LDI R2, 1
STR R2, [0x1016]
LDI R2, 2
STR R2, [0x1017]
LDI R2, 3
STR R2, [0x1018]
LDI R2, 1
STR R2, [0x1019]

; Основной цикл свертки
LDI R1, 0          ; R1 = 0 (индекс)

LOOP_START:
LDI R2, 10         ; R2 = 10 (размер массивов)
CMP R1, R2         ; Сравнить индекс с размером
JZ LOOP_END        ; Если индекс == размер, выйти из цикла

; Загрузить A[i]
ADD R3, R1, 0x1000 ; R3 = R1 + 0x1000 (адрес A[i])
LDRR R4, [R3]      ; R4 = A[i]

; Загрузить B[i]
ADD R3, R1, 0x1010 ; R3 = R1 + 0x1010 (адрес B[i])
LDRR R5, [R3]      ; R5 = B[i]

; Вычислить произведение
MUL R6, R4, R5     ; R6 = A[i] * B[i]

; Добавить к сумме
ADD R0, R0, R6     ; R0 = R0 + A[i] * B[i]

; Увеличить индекс
ADD R1, R1, 1      ; R1 = R1 + 1

JMP LOOP_START     ; Переход к началу цикла

LOOP_END:
; Сохранить результат
STR R0, [0x1100]   ; [0x1100] = результат
HALT
        """.strip()
    
    def _generate_sum_test_data(self) -> List[int]:
        """Генерирует тестовые данные для суммы массива"""
        # Массив: [7, 10, 20, 30, 40, 50, 60, 70]
        # Размер массива: 7, элементы: [10, 20, 30, 40, 50, 60, 70]
        # Ожидаемая сумма: 280
        return [7, 10, 20, 30, 40, 50, 60, 70]
    
    def _generate_convolution_test_data(self) -> List[int]:
        """Генерирует тестовые данные для свертки массивов"""
        # Массив A: [2, 3, 1, 4, 5, 2, 3, 1, 4, 2]
        a_vals = [2, 3, 1, 4, 5, 2, 3, 1, 4, 2]
        # Массив B: [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
        b_vals = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
        # Ожидаемый результат: 2*1 + 3*2 + 1*3 + 4*1 + 5*2 + 2*3 + 3*1 + 1*2 + 4*3 + 2*1 = 50
        return [10, *a_vals, 10, *b_vals]  # 10 - размер каждого массива
    
    def setup_task_data(self, processor: RISCProcessor, task_id: int):
        """Настроить данные для задачи в процессоре"""
        print(f"=== setup_task_data called for task {task_id} ===")
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        test_data = task["test_data"]
        print(f"Setting up task {task_id} data: {test_data}")
        
        if task_id == 1:  # Сумма массива
            # Формат: [размер, элемент1, элемент2, ...]
            size = test_data[0]
            elements = test_data[1:1 + size]
            
            print(f"Task 1 data: size={size}, elements={elements}")
            
            # Загружаем массив в память начиная с 0x1000
            # [0x1000] = размер массива
            processor.memory.ram[0x1000] = size
            print(f"Stored size={size} at address 0x1000")
            
            # [0x1001..0x1000+size] = элементы массива
            for i, value in enumerate(elements):
                processor.memory.ram[0x1000 + i + 1] = value
                print(f"Stored element[{i}] = {value} at address 0x{0x1000 + i + 1:04X}")
            
        elif task_id == 2:  # Свертка массивов
            # Формат: [size_a, a1..aN, size_b, b1..bM]
            size_a = test_data[0]
            a_vals = test_data[1:1 + size_a]
            size_b = test_data[1 + size_a]
            b_vals = test_data[2 + size_a:2 + size_a + size_b]

            print(f"Task 2 data: size_a={size_a}, a_vals={a_vals}, size_b={size_b}, b_vals={b_vals}")

            # Загружаем массив A в память (0x1000-0x1009)
            for i, v in enumerate(a_vals):
                processor.memory.ram[0x1000 + i] = v
                print(f"Stored A[{i}] = {v} at address 0x{0x1000 + i:04X}")

            # Загружаем массив B в память (0x1010-0x1019)
            for i, v in enumerate(b_vals):
                processor.memory.ram[0x1010 + i] = v
                print(f"Stored B[{i}] = {v} at address 0x{0x1010 + i:04X}")
            
            print(f"Memory after setup: A={processor.memory.ram[0x1000:0x100A]}, B={processor.memory.ram[0x1010:0x101A]}")
        
        print(f"Memory after setup: {processor.memory.ram[0x1000:0x1020]}")
    
    def verify_task_result(self, processor: RISCProcessor, task_id: int) -> Dict[str, Any]:
        """Проверить результат выполнения задачи"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        result = {
            "task_id": task_id,
            "success": False,
            "expected": None,
            "actual": None,
            "error": None
        }
        
        try:
            if task_id == 1:  # Сумма массива
                # Ожидаемая сумма: 10+20+30+40+50+60+70 = 280
                expected_sum = 280
                # Получаем результат из R0 (аккумулятор)
                actual_sum = processor.processor.registers[0]
                
                result["expected"] = expected_sum
                result["actual"] = actual_sum
                result["success"] = (expected_sum == actual_sum)
                
            elif task_id == 2:  # Свертка массивов
                # Ожидаемая свертка: 50
                expected_conv = 50
                
                # Получаем результат из памяти
                actual_conv = processor.memory.ram[0x1100]
                
                result["expected"] = expected_conv
                result["actual"] = actual_conv
                result["success"] = (expected_conv == actual_conv)
        
        except Exception as e:
            result["error"] = str(e)
        
        return result