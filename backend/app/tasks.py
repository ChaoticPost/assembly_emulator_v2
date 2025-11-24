"""
Предустановленные задачи для эмулятора двухадресного RISC процессора
"""
from typing import List, Dict, Any
from .processor import RISCProcessor
from .models import MemoryState

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
LDI R1, 1          ; R1 = 1 (индекс, начинается с 1, так как [0x0100] - размер)
LDI R2, 0x0100     ; R2 = базовый адрес массива

; Загрузка размера массива
LDR R3, [0x0100]   ; R3 = размер массива (из [0x0100])

; Основной цикл
LOOP_START:
; Сравниваем индекс с (размер + 1)
; Если индекс == размер + 1, значит обработали все элементы, выходим
ADD R4, R3, 1      ; R4 = размер + 1
CMP R1, R4         ; Сравнить индекс с (размер + 1)
JZ LOOP_END        ; Если индекс == размер + 1, выйти из цикла

; Вычисляем адрес текущего элемента: базовый_адрес + индекс
ADD R5, R2, R1     ; R5 = 0x0100 + индекс (адрес элемента)
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
; Массив A: [10, 2, 3, 1, 4, 5, 2, 3, 1, 4, 2] (размер=10, элементы: 2, 3, 1, 4, 5, 2, 3, 1, 4, 2)
; Массив B: [10, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1] (размер=10, элементы: 1, 2, 3, 1, 2, 3, 1, 2, 3, 1)
; Ожидаемый результат: 2*1 + 3*2 + 1*3 + 4*1 + 5*2 + 2*3 + 3*1 + 1*2 + 4*3 + 2*1 = 50

; Инициализация
LDI R0, 0          ; R0 = 0 (аккумулятор для свертки)
LDI R1, 1          ; R1 = 1 (индекс, начинается с 1, так как [0x0200] и [0x0300] - размеры)
LDI R2, 0x0200     ; R2 = базовый адрес массива A
LDI R3, 0x0300     ; R3 = базовый адрес массива B

; Загрузка размера массивов (размеры должны быть одинаковыми)
LDR R4, [0x0200]   ; R4 = размер массива A (из [0x0200])

; Основной цикл свертки
LOOP_START:
; Сравниваем индекс с (размер + 1)
; Если индекс == размер + 1, значит обработали все элементы, выходим
ADD R5, R4, 1      ; R5 = размер + 1
CMP R1, R5         ; Сравнить индекс с (размер + 1)
JZ LOOP_END        ; Если индекс == размер + 1, выйти из цикла

; Вычисляем адрес текущего элемента массива A: базовый_адрес_A + индекс
ADD R6, R2, R1     ; R6 = 0x0200 + индекс (адрес элемента A)
LDRR R7, [R6]      ; R7 = A[i] (значение элемента массива A)

; Вычисляем адрес текущего элемента массива B: базовый_адрес_B + индекс
ADD R6, R3, R1     ; R6 = 0x0300 + индекс (адрес элемента B)
LDRR R6, [R6]      ; R6 = B[i] (значение элемента массива B)

; Умножение A[i] × B[i]
MUL R7, R7, R6     ; R7 = A[i] × B[i]

; Добавляем произведение к свертке
ADD R0, R0, R7     ; R0 = R0 + A[i] × B[i] (свертка)

; Увеличиваем индекс
ADD R1, R1, 1      ; R1 = R1 + 1

JMP LOOP_START     ; Переход к началу цикла

LOOP_END:
; Результат в R0 (аккумулятор)
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
        print(f"DEBUG setup_task_data: processor.memory.ram exists={processor.memory.ram is not None}")
        print(f"DEBUG setup_task_data: processor.memory.ram length={len(processor.memory.ram) if processor.memory.ram else 0}")
        
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
            
            # Убеждаемся, что память инициализирована
            if not processor.memory.ram:
                print(f"WARNING: memory.ram is None or empty, initializing")
                processor.memory.ram = [0] * processor.memory_size
            
            # Убеждаемся, что память достаточно большая
            required_size = 0x0100 + len(elements) + 2
            current_size = len(processor.memory.ram) if processor.memory.ram else 0
            if current_size < required_size:
                print(f"WARNING: Memory too small ({current_size}), expanding to {required_size}")
                # Создаем новый список памяти с расширением
                new_ram = list(processor.memory.ram) if processor.memory.ram else [0] * processor.memory_size
                new_ram.extend([0] * (required_size - len(new_ram)))
                processor.memory.ram = new_ram
            
            # Создаем новый список памяти для гарантии обновления (Pydantic требует нового объекта)
            new_ram = list(processor.memory.ram) if processor.memory.ram else [0] * max(required_size, processor.memory_size)
            
            # Гарантируем достаточный размер
            while len(new_ram) < required_size:
                new_ram.append(0)
            
            # Загружаем массив в память начиная с 0x0100
            # [0x0100] = размер массива
            new_ram[0x0100] = int(size) & 0xFFFF
            print(f"Stored size=0x{size:04X} (decimal {size}) at address 0x0100")
            print(f"DEBUG: new_ram[0x0100] = {new_ram[0x0100]}, memory_size={len(new_ram)}")
            
            # [0x0101..0x0100+size] = элементы массива
            for i, value in enumerate(elements):
                addr = 0x0100 + i + 1
                if addr < len(new_ram):
                    new_ram[addr] = int(value) & 0xFFFF
                    print(f"Stored element[{i}] = 0x{value:04X} (decimal {value}) at address 0x{addr:04X}")
                else:
                    print(f"ERROR: Address 0x{addr:04X} out of bounds! memory_size={len(new_ram)}")
            
            # Присваиваем новый список памяти (Pydantic увидит изменение)
            # ВАЖНО: создаем полностью новый список для Pydantic
            processor.memory.ram = list(new_ram)  # Создаем новый список
            
            # Проверяем, что данные действительно загружены СРАЗУ после присваивания
            if 0x0100 < len(processor.memory.ram):
                verify_val = processor.memory.ram[0x0100]
                print(f"VERIFY: memory.ram[0x0100] = {verify_val} (0x{verify_val:04X}), expected={size}")
                
                # Проверяем все элементы массива
                all_ok = True
                for i, expected_value in enumerate(elements):
                    addr = 0x0100 + i + 1
                    if addr < len(processor.memory.ram):
                        actual_val = processor.memory.ram[addr]
                        if actual_val != expected_value:
                            print(f"ERROR: memory.ram[0x{addr:04X}] = {actual_val}, expected={expected_value}")
                            all_ok = False
                        else:
                            print(f"OK: memory.ram[0x{addr:04X}] = {actual_val} (0x{actual_val:04X}) ✓")
                    else:
                        print(f"ERROR: Address 0x{addr:04X} out of bounds for verification!")
                        all_ok = False
                
                # Если данные не записались, принудительно исправляем
                if verify_val != size or not all_ok:
                    print(f"ERROR: Данные не совпадают! Принудительно исправляем память")
                    # Создаем новый список с правильными данными
                    fixed_ram = list(processor.memory.ram)
                    # Гарантируем достаточный размер
                    while len(fixed_ram) < required_size:
                        fixed_ram.append(0)
                    # Устанавливаем размер
                    fixed_ram[0x0100] = int(size) & 0xFFFF
                    # Обновляем элементы массива
                    for i, value in enumerate(elements):
                        addr = 0x0100 + i + 1
                        if addr < len(fixed_ram):
                            fixed_ram[addr] = int(value) & 0xFFFF
                            print(f"FORCE FIX: fixed_ram[0x{addr:04X}] = {value} (0x{value:04X})")
                    # Присваиваем исправленную память (создаем новый объект для Pydantic)
                    from .models import MemoryState
                    processor.memory = MemoryState(ram=fixed_ram, history=processor.memory.history)
                    last_addr = 0x0100 + len(elements)
                    last_val = processor.memory.ram[last_addr] if last_addr < len(processor.memory.ram) else 'OUT_OF_BOUNDS'
                    print(f"FORCE FIX: Память исправлена, проверка: memory.ram[0x0100]={processor.memory.ram[0x0100]}, memory.ram[0x{last_addr:04X}]={last_val}")
                else:
                    print(f"OK: Все данные успешно записаны в память")
            else:
                print(f"ERROR: Cannot verify - memory too small! memory_size={len(processor.memory.ram)}")
            
        elif task_id == 2:  # Свертка массивов
            # Формат: [size_a, a1..aN, size_b, b1..bM]
            size_a = test_data[0]
            a_vals = test_data[1:1 + size_a]
            size_b = test_data[1 + size_a]
            b_vals = test_data[2 + size_a:2 + size_a + size_b]

            print(f"Task 2 data: size_a={size_a}, a_vals={a_vals}, size_b={size_b}, b_vals={b_vals}")

            # Убеждаемся, что память инициализирована
            if not processor.memory.ram:
                print(f"WARNING: memory.ram is None or empty, initializing")
                processor.memory.ram = [0] * processor.memory_size
            
            # Убеждаемся, что память достаточно большая
            required_size = max(0x020A, 0x030A) + 2
            current_size = len(processor.memory.ram) if processor.memory.ram else 0
            if current_size < required_size:
                print(f"WARNING: Memory too small ({current_size}), expanding to {required_size}")
                new_ram = list(processor.memory.ram) if processor.memory.ram else [0] * processor.memory_size
                new_ram.extend([0] * (required_size - len(new_ram)))
                processor.memory.ram = new_ram
            
            # Создаем новый список памяти для гарантии обновления (Pydantic требует нового объекта)
            new_ram = list(processor.memory.ram) if processor.memory.ram else [0] * max(required_size, processor.memory_size)
            
            # Гарантируем достаточный размер
            while len(new_ram) < required_size:
                new_ram.append(0)
            
            # Загружаем массив A в память (0x0200-0x020A)
            # [0x0200] = размер массива A
            new_ram[0x0200] = int(size_a) & 0xFFFF
            print(f"Stored size A=0x{size_a:04X} (decimal {size_a}) at address 0x0200")
            
            # [0x0201..0x020A] = элементы массива A
            for i, v in enumerate(a_vals):
                addr = 0x0200 + i + 1
                if addr < len(new_ram):
                    new_ram[addr] = int(v) & 0xFFFF
                    print(f"Stored A[{i}] = 0x{v:04X} (decimal {v}) at address 0x{addr:04X}")
                else:
                    print(f"ERROR: Address 0x{addr:04X} out of bounds! memory_size={len(new_ram)}")
            
            # Загружаем массив B в память (0x0300-0x030A)
            # [0x0300] = размер массива B
            new_ram[0x0300] = int(size_b) & 0xFFFF
            print(f"Stored size B=0x{size_b:04X} (decimal {size_b}) at address 0x0300")
            
            # [0x0301..0x030A] = элементы массива B
            for i, v in enumerate(b_vals):
                addr = 0x0300 + i + 1
                if addr < len(new_ram):
                    new_ram[addr] = int(v) & 0xFFFF
                    print(f"Stored B[{i}] = 0x{v:04X} (decimal {v}) at address 0x{addr:04X}")
                else:
                    print(f"ERROR: Address 0x{addr:04X} out of bounds! memory_size={len(new_ram)}")
            
            # Присваиваем новый список памяти (Pydantic увидит изменение)
            processor.memory.ram = list(new_ram)
            
            # Проверяем, что данные действительно загружены
            if 0x0200 < len(processor.memory.ram) and 0x0300 < len(processor.memory.ram):
                verify_size_a = processor.memory.ram[0x0200]
                verify_size_b = processor.memory.ram[0x0300]
                print(f"VERIFY: memory.ram[0x0200] = {verify_size_a} (0x{verify_size_a:04X}), expected={size_a}")
                print(f"VERIFY: memory.ram[0x0300] = {verify_size_b} (0x{verify_size_b:04X}), expected={size_b}")
            
            a_mem = [f"0x{v:04X}" for v in processor.memory.ram[0x0200:0x020B]] if len(processor.memory.ram) > 0x020A else []
            b_mem = [f"0x{v:04X}" for v in processor.memory.ram[0x0300:0x030B]] if len(processor.memory.ram) > 0x030A else []
            print(f"Memory after setup: A={a_mem}, B={b_mem}")
        
        mem_hex = [f"0x{v:04X}" for v in processor.memory.ram[0x1000:0x1020]]
        print(f"Memory after setup: {mem_hex}")
    
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
                # Вычисляем ожидаемую сумму динамически из test_data
                test_data = task["test_data"]
                if not test_data or len(test_data) < 2:
                    result["error"] = f"Invalid test_data for task 1: {test_data}"
                    return result
                
                # Формат: [размер, элемент1, элемент2, ...]
                size = test_data[0]
                elements = test_data[1:1 + size]  # Пропускаем размер, берем только элементы
                
                # Вычисляем ожидаемую сумму элементов
                expected_sum = sum(elements)
                
                # Получаем результат из R0 (аккумулятор)
                actual_sum = processor.processor.registers[0]
                
                result["expected"] = expected_sum
                result["actual"] = actual_sum
                result["success"] = (expected_sum == actual_sum)
                
            elif task_id == 2:  # Свертка массивов
                # Вычисляем ожидаемую свертку динамически из test_data
                test_data = task["test_data"]
                if not test_data or len(test_data) < 2:
                    result["error"] = f"Invalid test_data for task 2: {test_data}"
                    return result
                
                # Формат: [size_a, a1..aN, size_b, b1..bM]
                size_a = test_data[0]
                a_vals = test_data[1:1 + size_a]
                size_b = test_data[1 + size_a]
                b_vals = test_data[2 + size_a:2 + size_a + size_b]
                
                # Вычисляем ожидаемую свертку: Σ(A[i] × B[i])
                expected_conv = sum(a_vals[i] * b_vals[i] for i in range(min(len(a_vals), len(b_vals))))
                
                # Получаем результат из R0 (аккумулятор)
                actual_conv = processor.processor.registers[0]
                
                result["expected"] = expected_conv
                result["actual"] = actual_conv
                result["success"] = (expected_conv == actual_conv)
        
        except Exception as e:
            result["error"] = str(e)
        
        return result