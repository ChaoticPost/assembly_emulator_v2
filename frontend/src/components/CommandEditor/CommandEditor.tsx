// ADD: Command editor component for assembly code input and display
import React, { useState, useEffect } from 'react';
import { Card, Button, Textarea } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import { apiService } from '../../services/api';
import './CommandEditor.css';

export const CommandEditor: React.FC = () => {
  const { state, setSourceCode, compileCode, loading, error, current_task, setCurrentTask } = useEmulatorStore();
  const [assemblyCode, setAssemblyCode] = useState(state.source_code);
  const [activeTab, setActiveTab] = useState<'editor' | 'examples' | 'help'>('editor');
  const [exampleCode, setExampleCode] = useState<string>('');
  const [loadingExample, setLoadingExample] = useState(false);
  const [compileSuccess, setCompileSuccess] = useState(false);
  const [selectedTask, setSelectedTask] = useState<number | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<boolean>(false);
  const [task1Variant, setTask1Variant] = useState<'example' | 'template' | null>(null);
  const [task2Variant, setTask2Variant] = useState<'example' | 'template' | null>(null);

  const handleCodeChange = (code: string) => {
    setAssemblyCode(code);
    setSourceCode(code);
  };

  const handleCompile = async () => {
    setCompileSuccess(false);
    try {
      await compileCode(assemblyCode);
      setCompileSuccess(true);
      // Автоматически скрываем сообщение об успехе через 3 секунды
      setTimeout(() => setCompileSuccess(false), 3000);
    } catch (error) {
      setCompileSuccess(false);
    }
  };

  const handleLoadExample = async () => {
    if (!current_task) {
      console.warn('Не выбрана задача для загрузки примера');
      return;
    }

    try {
      setLoadingExample(true);
      const result = await apiService.getTaskProgram(current_task);
      setExampleCode(result.program);
      setActiveTab('examples');
    } catch (error) {
      console.error('Ошибка загрузки примера:', error);
    } finally {
      setLoadingExample(false);
    }
  };

  const handleTaskSelect = async (taskId: number) => {
    if (taskId === selectedTask) {
      // Если та же задача выбрана снова, снимаем выбор
      setSelectedTask(null);
      setSelectedTemplate(false);
      setTask1Variant(null);
      setTask2Variant(null);
      setExampleCode('');
      await setCurrentTask(null); // ВАЖНО: сбрасываем current_task в store
    } else {
      // Выбираем новую задачу
      setSelectedTask(taskId);
      setSelectedTemplate(false);
      if (taskId === 1) {
        // Для задачи 1 не загружаем пример автоматически, ждем выбора варианта
        setTask1Variant(null);
        setTask2Variant(null);
        setExampleCode('');
        await setCurrentTask(null);
      } else if (taskId === 2) {
        // Для задачи 2 не загружаем пример автоматически, ждем выбора варианта
        setTask1Variant(null);
        setTask2Variant(null);
        setExampleCode('');
        await setCurrentTask(null);
      } else {
        // Для других задач загружаем пример сразу
        setTask1Variant(null);
        setTask2Variant(null);
        await setCurrentTask(taskId); // ВАЖНО: устанавливаем current_task в store
        handleLoadTaskExample(taskId);
      }
    }
  };

  const handleTask1VariantSelect = async (variant: 'example' | 'template') => {
    if (task1Variant === variant) {
      // Если тот же вариант выбран, снимаем выбор
      setTask1Variant(null);
      setExampleCode('');
      await setCurrentTask(null);
    } else {
      // Выбираем новый вариант
      setTask1Variant(variant);
      // Для обоих вариантов устанавливаем current_task = 1, чтобы результат отображался
      await setCurrentTask(1);
      if (variant === 'example') {
        // Загружаем пример задачи 1
        handleLoadTaskExample(1);
      } else {
        // Загружаем шаблон
        handleLoadTemplate();
      }
    }
  };

  const handleTask2VariantSelect = async (variant: 'example' | 'template') => {
    if (task2Variant === variant) {
      // Если тот же вариант выбран, снимаем выбор
      setTask2Variant(null);
      setExampleCode('');
      await setCurrentTask(null);
    } else {
      // Выбираем новый вариант
      setTask2Variant(variant);
      // Для обоих вариантов устанавливаем current_task = 2, чтобы результат отображался
      await setCurrentTask(2);
      if (variant === 'example') {
        // Загружаем пример задачи 2
        handleLoadTaskExample(2);
      } else {
        // Загружаем шаблон
        handleLoadTask2Template();
      }
    }
  };

  const handleLoadTaskExample = (taskId: number) => {
    const examples = {
      1: `; Программа для вычисления суммы элементов массива
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
HALT`,

      'template': `; Программа для вычисления суммы элементов массива
; Массив: [7, 15, 20, 30, 40, 50, 60, 70] (размер=7, элементы: 15-70)
; Ожидаемый результат: 285 (15+20+30+40+50+60+70)

; Инициализация массива
LDI R7, 7           ; Размер массива = 7
STR R7, [0x0100]    ; Сохраняем размер по адресу 0x0100

LDI R7, 15          ; Элемент 1 = 15
STR R7, [0x0101]    ; Адрес 0x0101

LDI R7, 20          ; Элемент 2 = 20
STR R7, [0x0102]    ; Адрес 0x0102

LDI R7, 30          ; Элемент 3 = 30
STR R7, [0x0103]    ; Адрес 0x0103

LDI R7, 40          ; Элемент 4 = 40
STR R7, [0x0104]    ; Адрес 0x0104

LDI R7, 50          ; Элемент 5 = 50
STR R7, [0x0105]    ; Адрес 0x0105

LDI R7, 60          ; Элемент 6 = 60
STR R7, [0x0106]    ; Адрес 0x0106

LDI R7, 70          ; Элемент 7 = 70
STR R7, [0x0107]    ; Адрес 0x0107

; Основная программа вычисления суммы
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
HALT`,

      2: `; Программа для вычисления свертки двух массивов
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
HALT`
    };

    setExampleCode(examples[taskId as keyof typeof examples] || '');
  };

  const handleLoadTemplate = () => {
    // Загружаем шаблон с ручной инициализацией массива
    const template = `; Программа для вычисления суммы элементов массива
; Массив: [7, 15, 20, 30, 40, 50, 60, 70] (размер=7, элементы: 15-70)
; Ожидаемый результат: 285 (15+20+30+40+50+60+70)

; Инициализация массива
LDI R7, 7           ; Размер массива = 7
STR R7, [0x0100]    ; Сохраняем размер по адресу 0x0100

LDI R7, 15          ; Элемент 1 = 15
STR R7, [0x0101]    ; Адрес 0x0101

LDI R7, 20          ; Элемент 2 = 20
STR R7, [0x0102]    ; Адрес 0x0102

LDI R7, 30          ; Элемент 3 = 30
STR R7, [0x0103]    ; Адрес 0x0103

LDI R7, 40          ; Элемент 4 = 40
STR R7, [0x0104]    ; Адрес 0x0104

LDI R7, 50          ; Элемент 5 = 50
STR R7, [0x0105]    ; Адрес 0x0105

LDI R7, 60          ; Элемент 6 = 60
STR R7, [0x0106]    ; Адрес 0x0106

LDI R7, 70          ; Элемент 7 = 70
STR R7, [0x0107]    ; Адрес 0x0107

; Основная программа вычисления суммы
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
HALT`;
    setExampleCode(template);
  };

  const handleLoadTask2Template = () => {
    // Загружаем шаблон с ручной инициализацией массивов
    const template = `; Программа для вычисления свертки двух массивов
; Массив A: [10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (размер=10, элементы: 1-10)
; Массив B: [10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] (размер=10, элементы: все 1)
; Ожидаемый результат: 55 (1+2+3+4+5+6+7+8+9+10)

; Инициализация массива A
LDI R7, 10          ; Размер массива A = 10
STR R7, [0x0200]    ; Сохраняем размер по адресу 0x0200

LDI R7, 1           ; Элемент A[0] = 1
STR R7, [0x0201]    ; Адрес 0x0201

LDI R7, 2           ; Элемент A[1] = 2
STR R7, [0x0202]    ; Адрес 0x0202

LDI R7, 3           ; Элемент A[2] = 3
STR R7, [0x0203]    ; Адрес 0x0203

LDI R7, 4           ; Элемент A[3] = 4
STR R7, [0x0204]    ; Адрес 0x0204

LDI R7, 5           ; Элемент A[4] = 5
STR R7, [0x0205]    ; Адрес 0x0205

LDI R7, 6           ; Элемент A[5] = 6
STR R7, [0x0206]    ; Адрес 0x0206

LDI R7, 7           ; Элемент A[6] = 7
STR R7, [0x0207]    ; Адрес 0x0207

LDI R7, 8           ; Элемент A[7] = 8
STR R7, [0x0208]    ; Адрес 0x0208

LDI R7, 9           ; Элемент A[8] = 9
STR R7, [0x0209]    ; Адрес 0x0209

LDI R7, 10          ; Элемент A[9] = 10
STR R7, [0x020A]    ; Адрес 0x020A

; Инициализация массива B
LDI R7, 10          ; Размер массива B = 10
STR R7, [0x0300]    ; Сохраняем размер по адресу 0x0300

LDI R7, 1           ; Элемент B[0] = 1
STR R7, [0x0301]    ; Адрес 0x0301

LDI R7, 1           ; Элемент B[1] = 1
STR R7, [0x0302]    ; Адрес 0x0302

LDI R7, 1           ; Элемент B[2] = 1
STR R7, [0x0303]    ; Адрес 0x0303

LDI R7, 1           ; Элемент B[3] = 1
STR R7, [0x0304]    ; Адрес 0x0304

LDI R7, 1           ; Элемент B[4] = 1
STR R7, [0x0305]    ; Адрес 0x0305

LDI R7, 1           ; Элемент B[5] = 1
STR R7, [0x0306]    ; Адрес 0x0306

LDI R7, 1           ; Элемент B[6] = 1
STR R7, [0x0307]    ; Адрес 0x0307

LDI R7, 1           ; Элемент B[7] = 1
STR R7, [0x0308]    ; Адрес 0x0308

LDI R7, 1           ; Элемент B[8] = 1
STR R7, [0x0309]    ; Адрес 0x0309

LDI R7, 1           ; Элемент B[9] = 1
STR R7, [0x030A]    ; Адрес 0x030A

; Основная программа вычисления свертки
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
HALT`;
    setExampleCode(template);
  };

  const handleInsertExample = () => {
    setAssemblyCode(exampleCode);
    setSourceCode(exampleCode);
    setActiveTab('editor');
  };

  // Сбрасываем состояние компиляции при сбросе процессора
  useEffect(() => {
    if (state.processor.program_counter === 0 && state.processor.registers.every(r => r === 0)) {
      setCompileSuccess(false);
    }
  }, [state.processor.program_counter, state.processor.registers]);

  return (
    <Card className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h5 className="command-editor-title text-xl font-bold font-heading">Редактор команд</h5>
      </div>

      <div className="space-y-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              className={`border-b-2 py-2 px-1 text-sm font-bold ${activeTab === 'editor'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              onClick={() => setActiveTab('editor')}
            >
              Ассемблер
            </button>
            <button
              className={`border-b-2 py-2 px-1 text-sm font-bold ${activeTab === 'examples'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              onClick={() => setActiveTab('examples')}
            >
              Примеры
            </button>
            <button
              className={`border-b-2 py-2 px-1 text-sm font-bold ${activeTab === 'help'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              onClick={() => setActiveTab('help')}
            >
              Справка
            </button>
          </nav>
        </div>

        {activeTab === 'editor' ? (
          <div className="space-y-4">
            <Textarea
              value={assemblyCode}
              onChange={(e) => handleCodeChange(e.target.value)}
              rows={15}
              className="font-mono text-sm"
              placeholder="Введите код на ассемблере..."
            />
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {compileSuccess && !error && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 animate-fade-in">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p className="text-green-800 text-sm font-medium">Ошибок нет</p>
                </div>
              </div>
            )}

            <div className="flex space-x-3">
              <Button
                color="info"
                size="sm"
                onClick={handleCompile}
                disabled={loading}
                className="compile-button flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white border-0"
              >
                {loading ? (
                  <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                )}
                {loading ? 'Компиляция...' : 'Компилировать'}
              </Button>
              <Button
                color="light"
                size="sm"
                onClick={() => handleCodeChange('')}
                className="flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Очистить
              </Button>
            </div>
          </div>
        ) : activeTab === 'examples' ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-lg font-semibold text-green-900 font-heading">
                  Примеры кода для задач
                </h4>
                <Button
                  color="info"
                  size="sm"
                  onClick={handleLoadExample}
                  disabled={loadingExample || !current_task}
                  className="flex items-center space-x-2"
                >
                  {loadingExample ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  )}
                  {loadingExample ? 'Загрузка...' : 'Загрузить пример'}
                </Button>
              </div>
              <p className="text-green-800 text-sm mb-4 font-body">
                Готовые примеры кода для задач. Для задач 1 и 2 доступны два варианта: пример с автоматической загрузкой данных и шаблон с ручной инициализацией массивов.
              </p>

              {/* Радиокнопки для выбора заданий */}
              <div className="mb-4 space-y-2">
                <div className="task-selection-item">
                  <input
                    type="radio"
                    id="task-1"
                    name="task-selection"
                    checked={selectedTask === 1}
                    onChange={() => handleTaskSelect(1)}
                    className="task-selection-radio"
                  />
                  <label htmlFor="task-1" className="task-selection-label">
                    <div className="task-selection-title">Задача 1</div>
                    <div className="task-selection-description">Сумма массива</div>
                  </label>
                </div>

                {/* Подварианты для Задачи 1 */}
                {selectedTask === 1 && (
                  <div className="ml-8 space-y-2 mt-2">
                    <div className="task-selection-item">
                      <input
                        type="radio"
                        id="task-1-example"
                        name="task-1-variant"
                        checked={task1Variant === 'example'}
                        onChange={() => handleTask1VariantSelect('example')}
                        className="task-selection-radio"
                      />
                      <label htmlFor="task-1-example" className="task-selection-label">
                        <div className="task-selection-title">Пример</div>
                        <div className="task-selection-description">С автоматической загрузкой данных</div>
                      </label>
                    </div>
                    <div className="task-selection-item">
                      <input
                        type="radio"
                        id="task-1-template"
                        name="task-1-variant"
                        checked={task1Variant === 'template'}
                        onChange={() => handleTask1VariantSelect('template')}
                        className="task-selection-radio"
                      />
                      <label htmlFor="task-1-template" className="task-selection-label">
                        <div className="task-selection-title">Шаблон</div>
                        <div className="task-selection-description">С ручной инициализацией массива</div>
                      </label>
                    </div>
                  </div>
                )}

                <div className="task-selection-item">
                  <input
                    type="radio"
                    id="task-2"
                    name="task-selection"
                    checked={selectedTask === 2}
                    onChange={() => handleTaskSelect(2)}
                    className="task-selection-radio"
                  />
                  <label htmlFor="task-2" className="task-selection-label">
                    <div className="task-selection-title">Задача 2</div>
                    <div className="task-selection-description">Свертка массивов</div>
                  </label>
                </div>

                {/* Подварианты для Задачи 2 */}
                {selectedTask === 2 && (
                  <div className="ml-8 space-y-2 mt-2">
                    <div className="task-selection-item">
                      <input
                        type="radio"
                        id="task-2-example"
                        name="task-2-variant"
                        checked={task2Variant === 'example'}
                        onChange={() => handleTask2VariantSelect('example')}
                        className="task-selection-radio"
                      />
                      <label htmlFor="task-2-example" className="task-selection-label">
                        <div className="task-selection-title">Пример</div>
                        <div className="task-selection-description">С автоматической загрузкой данных</div>
                      </label>
                    </div>
                    <div className="task-selection-item">
                      <input
                        type="radio"
                        id="task-2-template"
                        name="task-2-variant"
                        checked={task2Variant === 'template'}
                        onChange={() => handleTask2VariantSelect('template')}
                        className="task-selection-radio"
                      />
                      <label htmlFor="task-2-template" className="task-selection-label">
                        <div className="task-selection-title">Шаблон</div>
                        <div className="task-selection-description">С ручной инициализацией массивов</div>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {exampleCode && (
              <div className="space-y-4">
                <Textarea
                  value={exampleCode}
                  readOnly
                  rows={15}
                  className="font-mono text-sm bg-gray-50"
                  placeholder="Код примера появится здесь..."
                />
                <div className="flex space-x-3">
                  <Button
                    color="success"
                    size="sm"
                    onClick={handleInsertExample}
                    className="insert-button flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                    </svg>
                    Вставить в редактор
                  </Button>
                  <Button
                    color="light"
                    size="sm"
                    onClick={() => setExampleCode('')}
                    className="flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Очистить
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h4 className="text-xl font-bold text-green-900 font-heading mb-4">
                📚 Справочник по ассемблеру RISC
              </h4>
              <p className="text-green-800 text-sm mb-4 font-body">
                Полное руководство по всем поддерживаемым инструкциям двухадресного RISC процессора
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Пересылка данных */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h5 className="text-lg font-semibold text-gray-900 font-heading mb-3 flex items-center">
                  <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">ДАННЫЕ</span>
                  Пересылка данных
                </h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">LDI rd, imm</code>
                    <span className="text-gray-600">загрузка константы в регистр</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">MOV rd, rs1</code>
                    <span className="text-gray-600">копирование регистра</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">LDR rd, [addr]</code>
                    <span className="text-gray-600">загрузка из памяти (прямая)</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">LDRR rd, [rs1]</code>
                    <span className="text-gray-600">загрузка из памяти (косвенная)</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <code className="font-mono text-green-600">STR rs1, [addr]</code>
                    <span className="text-gray-600">сохранение в память</span>
                  </div>
                </div>
              </div>

              {/* Арифметические операции */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h5 className="text-lg font-semibold text-gray-900 font-heading mb-3 flex items-center">
                  <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">МАТЕМАТИКА</span>
                  Арифметические операции
                </h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">ADD rd, rs1, rs2</code>
                    <span className="text-gray-600">сложение: rd = rs1 + rs2</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">SUB rd, rs1, rs2</code>
                    <span className="text-gray-600">вычитание: rd = rs1 - rs2</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">MUL rd, rs1, rs2</code>
                    <span className="text-gray-600">умножение: rd = rs1 * rs2</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <code className="font-mono text-green-600">DIV rd, rs1, rs2</code>
                    <span className="text-gray-600">деление: rd = rs1 / rs2</span>
                  </div>
                </div>
              </div>

              {/* Логические операции */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h5 className="text-lg font-semibold text-gray-900 font-heading mb-3 flex items-center">
                  <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">ЛОГИКА</span>
                  Логические операции
                </h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">AND rd, rs1, rs2</code>
                    <span className="text-gray-600">логическое И</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">OR rd, rs1, rs2</code>
                    <span className="text-gray-600">логическое ИЛИ</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">XOR rd, rs1, rs2</code>
                    <span className="text-gray-600">исключающее ИЛИ</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <code className="font-mono text-green-600">NOT rd, rs1</code>
                    <span className="text-gray-600">логическое НЕ</span>
                  </div>
                </div>
              </div>

              {/* Управление выполнением */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h5 className="text-lg font-semibold text-gray-900 font-heading mb-3 flex items-center">
                  <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">УПРАВЛЕНИЕ</span>
                  Переходы и сравнение
                </h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">CMP rs1, rs2</code>
                    <span className="text-gray-600">сравнение (устанавливает флаги)</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">JMP label</code>
                    <span className="text-gray-600">безусловный переход</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">JZ label</code>
                    <span className="text-gray-600">переход если Z=1</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-gray-100">
                    <code className="font-mono text-green-600">JNZ label</code>
                    <span className="text-gray-600">переход если Z=0</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <code className="font-mono text-green-600">HALT</code>
                    <span className="text-gray-600">остановка выполнения</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Режимы адресации */}
            <div className="bg-green-50 rounded-lg border border-green-200 p-6">
              <h5 className="text-lg font-semibold text-green-900 font-heading mb-4">
                🔧 Режимы адресации
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="bg-white rounded-lg p-3">
                  <strong className="text-green-800">Непосредственная:</strong>
                  <code className="block mt-1 font-mono text-green-600">LDI R0, 100</code>
                  <span className="text-gray-600 text-xs">Значение указано напрямую</span>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <strong className="text-green-800">Прямая:</strong>
                  <code className="block mt-1 font-mono text-green-600">LDR R0, [0x1000]</code>
                  <span className="text-gray-600 text-xs">Адрес указан напрямую</span>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <strong className="text-green-800">Регистровая:</strong>
                  <code className="block mt-1 font-mono text-green-600">ADD R0, R1, R2</code>
                  <span className="text-gray-600 text-xs">Операнд в регистре</span>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <strong className="text-green-800">Косвенно-регистровая:</strong>
                  <code className="block mt-1 font-mono text-green-600">LDRR R0, [R1]</code>
                  <span className="text-gray-600 text-xs">Адрес в регистре</span>
                </div>
              </div>
            </div>

            {/* Примеры использования */}
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
              <h5 className="text-lg font-semibold text-gray-900 font-heading mb-4">
                💡 Примеры использования
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h6 className="font-medium text-gray-800 mb-2">Простое сложение:</h6>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                    {`LDI R0, 5
LDI R1, 3
ADD R0, R0, R1
HALT`}
                  </pre>
                  <p className="text-xs text-gray-600 mt-1">Результат: R0 = 0x0008 (8)</p>
                </div>
                <div>
                  <h6 className="font-medium text-gray-800 mb-2">Условный переход:</h6>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                    {`LDI R0, 0
CMP R0, 0
JZ end
LDI R1, 1
end:
HALT`}
                  </pre>
                  <p className="text-xs text-gray-600 mt-1">Переход выполнится (R0 = 0)</p>
                </div>
              </div>
            </div>

            {/* Архитектура процессора */}
            <div className="bg-green-50 rounded-lg border border-green-200 p-6">
              <h5 className="text-lg font-semibold text-green-900 font-heading mb-4">
                🏗️ Архитектура процессора
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="bg-green-100 rounded-lg p-3 mb-2">
                    <div className="text-green-800 font-medium">Двухадресная RISC</div>
                  </div>
                  <p className="text-green-700">Операции с двумя операндами, результат в регистре</p>
                </div>
                <div className="text-center">
                  <div className="bg-green-100 rounded-lg p-3 mb-2">
                    <div className="text-green-800 font-medium">Фон-Неймана</div>
                  </div>
                  <p className="text-green-700">Единая память для команд и данных</p>
                </div>
                <div className="text-center">
                  <div className="bg-green-100 rounded-lg p-3 mb-2">
                    <div className="text-green-800 font-medium">8 регистров</div>
                  </div>
                  <p className="text-green-700">R0-R7 (R0 - аккумулятор)</p>
                </div>
              </div>
            </div>

            {/* Фазы выполнения команды */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
              <h5 className="text-xl font-bold text-blue-900 font-heading mb-4 flex items-center">
                <span className="mr-2">⚙️</span>
                Фазы выполнения команды
              </h5>
              <p className="text-blue-800 text-sm mb-4 font-body">
                Каждая команда выполняется в три этапа: выборка (Fetch), дешифрация (Decode) и исполнение (Execute)
              </p>

              <div className="space-y-4">
                {/* Фаза Fetch */}
                <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-500">
                  <div className="flex items-center mb-2">
                    <span className="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded mr-2">FETCH</span>
                    <h6 className="font-bold text-blue-800">Выборка</h6>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    Загрузка инструкции из памяти команд по адресу, указанному в счетчике команд (PC)
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded p-2 text-xs">
                    <strong className="text-blue-800">Что происходит:</strong>
                    <ul className="list-disc list-inside text-gray-700 mt-1 space-y-1">
                      <li>Чтение команды из <code className="font-mono text-blue-600">compiled_code[PC]</code></li>
                      <li>Загрузка команды в регистр команд (IR)</li>
                      <li>Регистры <strong>НЕ изменяются</strong></li>
                    </ul>
                  </div>
                </div>

                {/* Фаза Decode */}
                <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-yellow-500">
                  <div className="flex items-center mb-2">
                    <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-3 py-1 rounded mr-2">DECODE</span>
                    <h6 className="font-bold text-yellow-800">Дешифрация</h6>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    Дешифрация регистров и операндов, используемых в инструкции
                  </p>
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-xs">
                    <strong className="text-yellow-800">Что происходит:</strong>
                    <ul className="list-disc list-inside text-gray-700 mt-1 space-y-1">
                      <li>Парсинг команды на инструкцию и операнды</li>
                      <li>Определение режима адресации</li>
                      <li>Установка опкода команды в IR</li>
                      <li>Регистры <strong>НЕ изменяются</strong></li>
                    </ul>
                  </div>
                </div>

                {/* Фаза Execute */}
                <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-green-500">
                  <div className="flex items-center mb-2">
                    <span className="bg-green-100 text-green-800 text-xs font-bold px-3 py-1 rounded mr-2">EXECUTE</span>
                    <h6 className="font-bold text-green-800">Исполнение</h6>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    Выполнение операции: чтение регистров, выполнение операции в АЛУ, запись результата
                  </p>
                  <div className="bg-green-50 border border-green-200 rounded p-2 text-xs">
                    <strong className="text-green-800">Что происходит:</strong>
                    <ul className="list-disc list-inside text-gray-700 mt-1 space-y-1">
                      <li>Чтение регистра(ов) из банка регистров</li>
                      <li>Выполнение операций сдвига и АЛУ (арифметико-логическое устройство)</li>
                      <li>Обратная запись регистра(ов) в банк регистров</li>
                      <li>Обновление флагов состояния (Z, C, V, N)</li>
                      <li>Регистры <strong>МОГУТ изменяться</strong> в зависимости от команды</li>
                    </ul>
                  </div>
                </div>

                {/* Пример выполнения */}
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                  <h6 className="font-bold text-purple-800 mb-3">📋 Пример выполнения команды LDI R0, 7</h6>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2 bg-white rounded p-2">
                      <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">FETCH</span>
                      <span className="text-gray-700">Чтение команды "LDI R0, 7" из памяти, PC=0x0000</span>
                      <span className="text-gray-500 text-xs ml-auto">Регистры: R0=0x0000, R1=0x0000...</span>
                    </div>
                    <div className="flex items-center space-x-2 bg-white rounded p-2">
                      <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2 py-1 rounded">DECODE</span>
                      <span className="text-gray-700">Парсинг: инструкция=LDI, операнды=[R0, 7]</span>
                      <span className="text-gray-500 text-xs ml-auto">Регистры: R0=0x0000, R1=0x0000...</span>
                    </div>
                    <div className="flex items-center space-x-2 bg-white rounded p-2">
                      <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded">EXECUTE</span>
                      <span className="text-gray-700">Выполнение: R0 = 7</span>
                      <span className="text-green-600 font-bold text-xs ml-auto">Регистры: R0=0x0007 ⚠️, R1=0x0000...</span>
                    </div>
                  </div>
                  <p className="text-xs text-purple-700 mt-2">
                    💡 В интерфейсе каждая фаза отображается в отдельной строке таблицы "Пошаговое выполнение программы" с цветовой индикацией
                  </p>
                </div>
              </div>
            </div>

            {/* Как работает выполнение программы */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200 p-6">
              <h5 className="text-xl font-bold text-green-900 font-heading mb-4 flex items-center">
                <span className="mr-2">🎯</span>
                Как работает выполнение программы
              </h5>

              <div className="space-y-4">
                {/* Шаг 1 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h6 className="font-bold text-green-800 mb-2">1️⃣ Загрузка задачи</h6>
                  <p className="text-sm text-gray-700 mb-2">
                    Выберите задачу в панели "Задания" и нажмите <strong>"Загрузить данные для задачи"</strong> — данные загружаются в память, программа компилируется.
                  </p>
                  <div className="bg-green-50 border-l-4 border-green-500 p-2 text-sm">
                    <strong className="text-green-800">✅ Готово</strong> — программа и данные загружены!
                  </div>
                </div>

                {/* Шаг 2 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h6 className="font-bold text-green-800 mb-2">2️⃣ Пошаговое выполнение</h6>
                  <p className="text-sm text-gray-700 mb-2">
                    Нажимайте <strong>"Следующий шаг"</strong> для выполнения одной команды:
                  </p>
                  <ul className="text-sm text-gray-700 space-y-1 ml-4">
                    <li>📊 <strong>Счётчик команд (PC)</strong> увеличивается на 1</li>
                    <li>🔧 <strong>Регистр команд (IR)</strong> показывает текущую команду</li>
                    <li>💾 <strong>Регистры R0-R7</strong> обновляются с новыми значениями (в hex-формате)</li>
                    <li>🚩 <strong>Флаги (Z, C, V, N)</strong> меняются в зависимости от результата</li>
                  </ul>
                </div>

                {/* Шаг 3 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h6 className="font-bold text-green-800 mb-2">3️⃣ Визуализация в блоке "Память"</h6>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="bg-green-50 p-3 rounded">
                      <strong className="text-green-800">История выполнения:</strong>
                      <p className="text-gray-700 mt-1">
                        История каждого шага с состоянием регистров до и после выполнения команды
                      </p>
                    </div>
                    <div className="bg-green-50 p-3 rounded">
                      <strong className="text-green-800">Состояние памяти:</strong>
                      <p className="text-gray-700 mt-1">
                        Текущие данные в памяти с адресами и значениями ячеек
                      </p>
                    </div>
                  </div>
                </div>

                {/* Пример */}
                <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg p-4 border border-orange-200">
                  <h6 className="font-bold text-orange-800 mb-2">📝 Пример: LDI R0, 0x000A; LDI R1, 0x0003; ADD R0, R0, R1</h6>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="bg-green-500 text-white px-2 py-1 rounded font-mono text-xs">Шаг 1</span>
                      <span className="text-gray-700">LDI R0, 0x000A → R0 = <code className="text-green-600 font-bold">0x000A</code></span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="bg-green-500 text-white px-2 py-1 rounded font-mono text-xs">Шаг 2</span>
                      <span className="text-gray-700">LDI R1, 0x0003 → R1 = <code className="text-green-600 font-bold">0x0003</code></span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="bg-green-500 text-white px-2 py-1 rounded font-mono text-xs">Шаг 3</span>
                      <span className="text-gray-700">ADD R0, R0, R1 → R0 = <code className="text-green-600 font-bold">0x000D</code> (10+3)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
