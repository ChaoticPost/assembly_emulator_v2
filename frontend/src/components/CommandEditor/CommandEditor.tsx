// ADD: Command editor component for assembly code input and display
import React, { useState, useEffect } from 'react';
import { Card, Button, Textarea } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import { apiService } from '../../services/api';
import './CommandEditor.css';

export const CommandEditor: React.FC = () => {
  const { state, setSourceCode, compileCode, loading, error, current_task, setCurrentTask } = useEmulatorStore();
  const [assemblyCode, setAssemblyCode] = useState(state.source_code);
  const [activeTab, setActiveTab] = useState<'editor' | 'examples'>('editor');
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
      // Убеждаемся, что данные задачи загружены
      if (current_task) {
        await setCurrentTask(current_task);
      }
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
        // Загружаем пример задачи 1 из бэкенда
        try {
          setLoadingExample(true);
          const result = await apiService.getTaskProgram(1);
          setExampleCode(result.program);
          setActiveTab('examples');
        } catch (error) {
          console.error('Ошибка загрузки примера задачи 1:', error);
          // Fallback на локальный пример, если бэкенд недоступен
          handleLoadTaskExample(1);
        } finally {
          setLoadingExample(false);
        }
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
    // Fallback на локальные примеры, если бэкенд недоступен
    const examples = {
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
    // Загружаем шаблон с ручной инициализацией массива из 3 элементов
    const template = `; Поиск максимума в массиве
; Массив: [3, 10, 20, 30] (размер=3, элементы: 10, 20, 30)
; Ожидаемый результат: 30 (максимальный элемент)
; Шаблон с ручной инициализацией массива для быстрой проверки

; Инициализация массива (массив хранится в памяти начиная с адреса 0x0100)
LDI 3              ; ACC = 3 (размер массива)
STA 0x0100         ; сохранить размер по адресу 0x0100

LDI 10             ; ACC = 10 (элемент 1)
STA 0x0101         ; адрес 0x0101

LDI 20             ; ACC = 20 (элемент 2)
STA 0x0102         ; адрес 0x0102

LDI 30             ; ACC = 30 (элемент 3)
STA 0x0103         ; адрес 0x0103

; Основная программа поиска максимума
; Подготовка констант
LDI 1              ; ACC = 1
STA 0x0400         ; константа 1 в 0x0400

; Загрузить размер массива N из памяти[0x0100]
LDA 0x0100         ; ACC = размер массива (3)
STA 0x0410         ; сохранить размер во временную переменную

; Загрузить первый элемент в ACC как начальный максимум
LDA 0x0101         ; ACC = первый элемент (10) - начальный максимум
STA 0x0411         ; сохранить максимум в 0x0411

; Инициализировать индекс i = 2
LDI 2              ; ACC = 2
STA 0x0412         ; сохранить индекс в 0x0412

; Константы для сравнения индексов (для массива из 3 элементов нужны только 2 и 3)
LDI 2              ; константа для индекса 2
STA 0x0420
LDI 3              ; константа для индекса 3
STA 0x0421

; Основной цикл
LOOP_START:
; Проверка условия выхода: индекс > размер
LDA 0x0410         ; ACC = размер (3)
ADD 0x0400         ; ACC = размер + 1 (4)
STA 0x0430         ; сохранить (размер + 1) = 4
LDA 0x0412         ; ACC = индекс
CMP 0x0430         ; сравнить индекс с (размер + 1)
JZ LOOP_END        ; если индекс == 4, выйти из цикла

; Таблица переходов на основе индекса
; Для массива из 3 элементов обрабатываем индексы 2 и 3
LDA 0x0412         ; ACC = индекс
CMP 0x0420         ; сравнить с 2
JZ LOAD_ELEM_2     ; если индекс == 2, загрузить элемент [0x0102]
LDA 0x0412         ; ACC = индекс
CMP 0x0421         ; сравнить с 3
JZ LOAD_ELEM_3     ; если индекс == 3, загрузить элемент [0x0103]
JMP INCREMENT_INDEX ; иначе перейти к увеличению индекса

LOAD_ELEM_2:
LDA 0x0102         ; ACC = элемент массива по индексу 2 (20)
JMP COMPARE_MAX    ; перейти к сравнению с максимумом

LOAD_ELEM_3:
LDA 0x0103         ; ACC = элемент массива по индексу 3 (30)
JMP COMPARE_MAX    ; перейти к сравнению с максимумом

; Сравнить элемент с максимумом
COMPARE_MAX:
STA 0x0440         ; сохранить текущий элемент во временную переменную
LDA 0x0411         ; ACC = текущий максимум
CMP 0x0440         ; сравнить максимум с элементом (устанавливает флаги)
; Если максимум < элемент, то при вычитании будет заем → C=1 (Carry установлен)
JC UPDATE_MAX      ; если был заем (максимум < элемент), обновить максимум
JMP INCREMENT_INDEX ; иначе перейти к увеличению индекса

UPDATE_MAX:
LDA 0x0440         ; ACC = новый максимум (текущий элемент больше)
STA 0x0411         ; сохранить новый максимум в 0x0411
JMP INCREMENT_INDEX ; перейти к увеличению индекса

INCREMENT_INDEX:
LDA 0x0412         ; ACC = индекс
ADD 0x0400         ; ACC = индекс + 1
STA 0x0412         ; сохранить новый индекс

JMP LOOP_START     ; переход к началу цикла

LOOP_END:
LDA 0x0411         ; ACC = максимум (30)
HALT               ; остановка программы`;
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
    const isReset = state.processor.program_counter === 0 &&
      (state.processor.accumulator === 0 ||
        (state.processor.registers && state.processor.registers.length > 0 &&
          state.processor.registers.every(r => r === 0)));
    if (isReset) {
      setCompileSuccess(false);
    }
  }, [state.processor.program_counter, state.processor.accumulator, state.processor.registers]);

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
          </nav>
        </div>

        {activeTab === 'editor' && (
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
        )}
        {activeTab === 'examples' && (
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
                    <div className="task-selection-description">Поиск максимума в массиве</div>
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
        )}
      </div>
    </Card>
  );
};
