// ADD: Command editor component for assembly code input and display
import React, { useState, useEffect } from 'react';
import { Card, Button, Textarea } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import { apiService } from '../../services/api';
import './CommandEditor.css';

export const CommandEditor: React.FC = () => {
  const { state, setSourceCode, compileCode, loading, error, current_task } = useEmulatorStore();
  const [assemblyCode, setAssemblyCode] = useState(state.source_code);
  const [activeTab, setActiveTab] = useState<'editor' | 'examples' | 'help'>('editor');
  const [exampleCode, setExampleCode] = useState<string>('');
  const [loadingExample, setLoadingExample] = useState(false);
  const [compileSuccess, setCompileSuccess] = useState(false);
  const [selectedTask, setSelectedTask] = useState<number | null>(null);

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

  const handleTaskSelect = (taskId: number) => {
    if (taskId === selectedTask) {
      // Если та же задача выбрана снова, снимаем выбор
      setSelectedTask(null);
      setExampleCode('');
    } else {
      // Выбираем новую задачу и загружаем пример
      setSelectedTask(taskId);
      handleLoadTaskExample(taskId);
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

      2: `; Программа 2: Свертка двух массивов
; Массив A: [5, 1, 2, 3, 4, 5]
; Массив B: [5, 5, 4, 3, 2, 1]
; Ожидаемый результат: 1*5 + 2*4 + 3*3 + 4*2 + 5*1 = 35

; Инициализация
LDI R0, 0          ; R0 = 0 (аккумулятор для суммы свертки)
LDI R1, 1          ; R1 = 1 (индекс)
LDI R2, 0x1100     ; R2 = базовый адрес массива A
LDI R3, 0x1200     ; R3 = базовый адрес массива B

; Загрузка размера массива (размеры должны быть одинаковыми)
LDR R4, [0x1100]   ; R4 = размер массива A

; Основной цикл свертки
CONV_LOOP:
; Проверка условия выхода
ADD R5, R4, 1      ; R5 = размер + 1
CMP R1, R5         ; Сравнить индекс с (размер + 1)
JZ CONV_END        ; Если равно, выйти

; Загрузка элемента из массива A
ADD R6, R2, R1     ; R6 = адрес элемента A
LDRR R7, [R6]      ; R7 = значение A[i]

; Загрузка элемента из массива B
ADD R6, R3, R1     ; R6 = адрес элемента B
LDRR R6, [R6]      ; R6 = значение B[i]

; Умножение A[i] * B[i]
MUL R7, R7, R6     ; R7 = A[i] * B[i]

; Добавление к общей сумме
ADD R0, R0, R7     ; R0 = R0 + A[i]*B[i]

; Увеличение индекса
ADD R1, R1, 1      ; R1 = R1 + 1

JMP CONV_LOOP      ; Повторить цикл

CONV_END:
HALT

; Данные в памяти:
; Массив A по адресу 0x1100:
; [0x1100] = 5     (размер)
; [0x1101] = 1     (A[1])
; [0x1102] = 2     (A[2])
; [0x1103] = 3     (A[3])
; [0x1104] = 4     (A[4])
; [0x1105] = 5     (A[5])

; Массив B по адресу 0x1200:
; [0x1200] = 5     (размер)
; [0x1201] = 5     (B[1])
; [0x1202] = 4     (B[2])
; [0x1203] = 3     (B[3])
; [0x1204] = 2     (B[4])
; [0x1205] = 1     (B[5])`
    };

    setExampleCode(examples[taskId as keyof typeof examples] || '');
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
        <h5 className="text-xl font-bold text-white-900 font-heading">Редактор команд</h5>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Редактирование</span>
        </div>
      </div>

      <div className="space-y-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              className={`border-b-2 py-2 px-1 text-sm font-medium ${activeTab === 'editor'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              onClick={() => setActiveTab('editor')}
            >
              Ассемблер
            </button>
            <button
              className={`border-b-2 py-2 px-1 text-sm font-medium ${activeTab === 'examples'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              onClick={() => setActiveTab('examples')}
            >
              Примеры
            </button>
            <button
              className={`border-b-2 py-2 px-1 text-sm font-medium ${activeTab === 'help'
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
                className="flex items-center space-x-2"
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
                Готовые примеры кода для задач 1 и 2. Выберите задание и загрузите пример.
              </p>

              {/* Радиокнопки для выбора заданий (только одна задача) */}
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
                    className="flex items-center space-x-2"
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
