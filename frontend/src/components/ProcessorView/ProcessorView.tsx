import React, { useState, useEffect, useMemo } from 'react';
import { useEmulatorStore } from '../../store/emulatorStore';
import { apiService } from '../../services/api';
import './ProcessorView.css';

export const ProcessorView: React.FC = () => {
  const { state, current_task } = useEmulatorStore();
  const { processor } = state;
  const [previousCounter, setPreviousCounter] = useState(processor.program_counter);
  const [animateCounter, setAnimateCounter] = useState(false);
  const [taskTestData, setTaskTestData] = useState<number[] | null>(null);

  // Отладочная информация
  useEffect(() => {
    console.log('ProcessorView: состояние обновлено', {
      registers: processor.registers,
      registersLength: processor.registers?.length,
      pc: processor.program_counter,
      ir: processor.instruction_register,
      ir_asm: processor.instruction_register_asm,
      flags: processor.flags,
      cycles: processor.cycles
    });
  }, [processor]);

  // Получаем аккумулятор из состояния процессора
  const accumulator = useMemo(() => {
    // Используем accumulator если доступен, иначе берем из registers[0] для совместимости
    const acc = processor.accumulator !== undefined
      ? processor.accumulator
      : (processor.registers && processor.registers[0] !== undefined ? processor.registers[0] : 0);
    return acc;
  }, [processor.accumulator, processor.registers]);

  // Функция форматирования значений для отображения
  const formatValue = (value: number | undefined | null, isHex: boolean = false) => {
    // Обрабатываем undefined и null
    if (value === undefined || value === null) {
      return isHex ? '0x0000' : '0';
    }

    if (isHex) {
      // Ограничиваем значение 16-битным диапазоном (0x0000 - 0xFFFF)
      // Обрабатываем как положительные, так и отрицательные числа
      // Используем беззнаковое представление для отрицательных чисел
      const numValue = typeof value === 'number' ? value : 0;
      const unsigned = (numValue >>> 0) & 0xFFFF;
      const hexString = unsigned.toString(16).toUpperCase().padStart(4, '0');
      return `0x${hexString}`;
    }
    return value.toString();
  };

  // Состояния для отслеживания изменений флагов
  const [previousFlags, setPreviousFlags] = useState(processor.flags);
  const [animateFlags, setAnimateFlags] = useState({
    zero: false,
    carry: false,
    overflow: false,
    negative: false
  });

  // Отслеживаем изменения счетчика команд для анимации
  useEffect(() => {
    if (processor.program_counter !== previousCounter) {
      setAnimateCounter(true);
      setPreviousCounter(processor.program_counter);

      // Сбрасываем анимацию через 600ms
      setTimeout(() => setAnimateCounter(false), 600);
    }
  }, [processor.program_counter]);

  // Отслеживаем изменения флагов для анимации
  useEffect(() => {
    if (!processor.flags || !previousFlags) {
      setPreviousFlags(processor.flags || { zero: false, carry: false, overflow: false, negative: false });
      return;
    }

    const flagsChanged = {
      zero: processor.flags.zero !== previousFlags.zero,
      carry: processor.flags.carry !== previousFlags.carry,
      overflow: processor.flags.overflow !== previousFlags.overflow,
      negative: processor.flags.negative !== previousFlags.negative
    };

    // Если какой-либо флаг изменился
    if (flagsChanged.zero || flagsChanged.carry || flagsChanged.overflow || flagsChanged.negative) {
      setAnimateFlags(flagsChanged);
      setPreviousFlags(processor.flags);

      // Сбрасываем анимации через 800ms
      setTimeout(() => {
        setAnimateFlags({
          zero: false,
          carry: false,
          overflow: false,
          negative: false
        });
      }, 800);
    }
  }, [processor.flags, previousFlags]);

  // Загружаем test_data задачи при изменении current_task
  useEffect(() => {
    if (current_task) {
      apiService.getTaskProgram(current_task)
        .then((result) => {
          setTaskTestData(result.test_data);
        })
        .catch((error) => {
          console.warn('Не удалось загрузить test_data задачи:', error);
          setTaskTestData(null);
        });
    } else {
      setTaskTestData(null);
    }
  }, [current_task]);

  // Функция для формирования строки результата задачи 1
  const formatTask1Result = useMemo(() => {
    if (current_task !== 1) {
      return null;
    }

    // Сначала пытаемся получить данные из памяти (для шаблона с ручной инициализацией)
    let size: number | null = null;
    let elements: number[] = [];

    if (state.memory.ram && state.memory.ram.length > 0x0307) {
      // Читаем размер массива из памяти по адресу 0x0300
      const sizeValue = state.memory.ram[0x0300];
      if (sizeValue !== undefined && sizeValue !== null && sizeValue > 0 && sizeValue <= 15) {
        size = sizeValue;
        // Читаем элементы массива из памяти по адресам 0x0301-0x0307
        elements = [];
        for (let i = 1; i <= size; i++) {
          const addr = 0x0300 + i;
          if (addr < state.memory.ram.length) {
            const value = state.memory.ram[addr];
            if (value !== undefined && value !== null) {
              // Преобразуем в 16-битное беззнаковое число
              const unsignedValue = (value >>> 0) & 0xFFFF;
              // Если значение > 32767, считаем его отрицательным (дополнительный код)
              const signedValue = unsignedValue > 32767 ? unsignedValue - 65536 : unsignedValue;
              elements.push(signedValue);
            } else {
              elements.push(0);
            }
          } else {
            elements.push(0);
          }
        }
      }
    }

    // Если данные из памяти не получены, используем test_data (для примера с автоматической загрузкой)
    if (!size || elements.length === 0) {
      if (!taskTestData || taskTestData.length < 2) {
        return null;
      }
      // Формат: [размер, элемент1, элемент2, ...]
      size = taskTestData[0];
      elements = taskTestData.slice(1, 1 + size);
    }

    if (elements.length === 0) {
      return null;
    }

    const actualMax = accumulator || 0;

    // Формируем строку: максимум из [элемент1, элемент2, ...] = максимум (hex)
    const elementsStr = elements.join(', ');
    const hexMax = formatValue(actualMax, true);

    return `Максимум из [${elementsStr}] = ${actualMax} (${hexMax})`;
  }, [taskTestData, current_task, accumulator, state.memory.ram]);

  return (
    <div className="processor-view-container">
      <div className="processor-header">
        <h5 className="processor-title">Процессор</h5>
      </div>

      <div className="processor-grid-layout">
        {/* Аккумулятор */}
        <div className="processor-section special-registers-section">
          <div className="section-content">
            <label className="section-label">
              Аккумулятор (ACC)
            </label>
            <div className="special-register-value pc-value">
              {formatValue(accumulator, true)}
            </div>
          </div>
        </div>

        {/* Специальные регистры */}
        <div className="processor-section special-registers-section">
          <div className="section-content">
            <label className="section-label">
              Счётчик команд (PC)
              {animateCounter && (
                <span className="label-animation">↑ увеличивается</span>
              )}
            </label>
            <div className={`special-register-value pc-value ${animateCounter ? 'animate-counter-increase' : ''}`}>
              {processor.program_counter !== undefined && processor.program_counter !== null
                ? processor.program_counter
                : 0}
            </div>
          </div>

          <div className="section-content">
            <label className="section-label">
              Регистр команд (IR)
            </label>
            <div className="ir-value">
              <span className="ir-prefix">0x</span>
              <span className="ir-hex">
                {processor.instruction_register !== undefined && processor.instruction_register !== null
                  ? processor.instruction_register.toString(16).toUpperCase().padStart(4, '0')
                  : '0000'}
              </span>
            </div>
            {(processor.instruction_register_asm || processor.current_command) ? (
              <div className="ir-asm">
                <span className="ir-asm-label">Ассемблер:</span> {processor.instruction_register_asm || processor.current_command || 'NOP'}
              </div>
            ) : (
              <div className="ir-asm">
                <span className="ir-asm-label">Ассемблер:</span> <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>нет команды</span>
              </div>
            )}
          </div>
        </div>

        {/* Флаги состояния */}
        <div className="processor-section flags-section">
          <div className="section-content">
            <label className="section-label">
              {state.processor.is_halted && state.processor.cycles > 0 ? 'Итог' : 'Флаги состояния'}
            </label>
            {current_task === 1 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <>
                <div className="task-result">
                  <div className="task-result-value">
                    {formatValue(accumulator || 0, true)}
                  </div>
                  <div className="task-result-title">
                    Максимальный элемент массива
                  </div>
                  <div className="task-result-desc">
                    {formatTask1Result || `Результат: ${formatValue(accumulator, true)} (${accumulator || 0})`}
                  </div>
                </div>
                <div className="flags-grid" style={{ marginTop: '1.5rem' }}>
                  {/* Zero Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.zero ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.zero ? '1' : '0'}
                    </div>
                    <div className="flag-name">Zero</div>
                    <div className="flag-desc">
                      {processor.flags?.zero ? 'ноль' : 'не ноль'}
                    </div>
                  </div>

                  {/* Carry Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.carry ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.carry ? '1' : '0'}
                    </div>
                    <div className="flag-name">Carry</div>
                    <div className="flag-desc">
                      {processor.flags?.carry ? 'перенос' : 'нет переноса'}
                    </div>
                  </div>

                  {/* Overflow Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.overflow ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.overflow ? '1' : '0'}
                    </div>
                    <div className="flag-name">Overflow</div>
                    <div className="flag-desc">
                      {processor.flags?.overflow ? 'переполнение' : 'нет переполнения'}
                    </div>
                  </div>

                  {/* Negative Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.negative ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.negative ? '1' : '0'}
                    </div>
                    <div className="flag-name">Negative</div>
                    <div className="flag-desc">
                      {processor.flags?.negative ? 'отрицательное' : 'положительное'}
                    </div>
                  </div>
                </div>
              </>
            ) : current_task === 2 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <>
                <div className="task-result">
                  <div className="task-result-value">
                    {formatValue(accumulator || 0, true)}
                  </div>
                  <div className="task-result-title">
                    Свертка двух массивов
                  </div>
                  <div className="task-result-desc">
                    {`${accumulator || 0} в десятичной системе`}
                  </div>
                </div>
                <div className="flags-grid" style={{ marginTop: '1.5rem' }}>
                  {/* Zero Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.zero ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.zero ? '1' : '0'}
                    </div>
                    <div className="flag-name">Zero</div>
                    <div className="flag-desc">
                      {processor.flags?.zero ? 'ноль' : 'не ноль'}
                    </div>
                  </div>

                  {/* Carry Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.carry ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.carry ? '1' : '0'}
                    </div>
                    <div className="flag-name">Carry</div>
                    <div className="flag-desc">
                      {processor.flags?.carry ? 'перенос' : 'нет переноса'}
                    </div>
                  </div>

                  {/* Overflow Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.overflow ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.overflow ? '1' : '0'}
                    </div>
                    <div className="flag-name">Overflow</div>
                    <div className="flag-desc">
                      {processor.flags?.overflow ? 'переполнение' : 'нет переполнения'}
                    </div>
                  </div>

                  {/* Negative Flag */}
                  <div className="flag-item">
                    <div className={`flag-indicator ${processor.flags?.negative ? 'flag-active' : 'flag-inactive'}`}>
                      {processor.flags?.negative ? '1' : '0'}
                    </div>
                    <div className="flag-name">Negative</div>
                    <div className="flag-desc">
                      {processor.flags?.negative ? 'отрицательное' : 'положительное'}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flags-grid">
                {/* Zero Flag */}
                <div className="flag-item">
                  <div className={`flag-indicator ${processor.flags?.zero ? 'flag-active' : 'flag-inactive'} ${animateFlags.zero ? 'animate-counter-increase' : ''}`}>
                    {processor.flags?.zero ? '1' : '0'}
                  </div>
                  <div className="flag-name">Zero</div>
                  <div className="flag-desc">
                    {processor.flags?.zero ? 'ноль' : 'не ноль'}
                  </div>
                  {animateFlags.zero && (
                    <div className="flag-animation">↑</div>
                  )}
                </div>

                {/* Carry Flag */}
                <div className="flag-item">
                  <div className={`flag-indicator ${processor.flags?.carry ? 'flag-active' : 'flag-inactive'} ${animateFlags.carry ? 'animate-counter-increase' : ''}`}>
                    {processor.flags?.carry ? '1' : '0'}
                  </div>
                  <div className="flag-name">Carry</div>
                  <div className="flag-desc">
                    {processor.flags?.carry ? 'перенос' : 'нет переноса'}
                  </div>
                  {animateFlags.carry && (
                    <div className="flag-animation">↑</div>
                  )}
                </div>

                {/* Overflow Flag */}
                <div className="flag-item">
                  <div className={`flag-indicator ${processor.flags?.overflow ? 'flag-active' : 'flag-inactive'} ${animateFlags.overflow ? 'animate-counter-increase' : ''}`}>
                    {processor.flags?.overflow ? '1' : '0'}
                  </div>
                  <div className="flag-name">Overflow</div>
                  <div className="flag-desc">
                    {processor.flags?.overflow ? 'переполнение' : 'нет переполнения'}
                  </div>
                  {animateFlags.overflow && (
                    <div className="flag-animation">↑</div>
                  )}
                </div>

                {/* Negative Flag */}
                <div className="flag-item">
                  <div className={`flag-indicator ${processor.flags?.negative ? 'flag-active' : 'flag-inactive'} ${animateFlags.negative ? 'animate-counter-increase' : ''}`}>
                    {processor.flags?.negative ? '1' : '0'}
                  </div>
                  <div className="flag-name">Negative</div>
                  <div className="flag-desc">
                    {processor.flags?.negative ? 'отрицательное' : 'положительное'}
                  </div>
                  {animateFlags.negative && (
                    <div className="flag-animation">↑</div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="section-content">
            <label className="section-label">
              Циклы выполнения
            </label>
            <div className="special-register-value cycles-value">
              {processor.cycles}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};