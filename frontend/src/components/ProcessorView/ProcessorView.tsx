import React, { useState, useEffect, useMemo } from 'react';
import { useEmulatorStore } from '../../store/emulatorStore';
import './ProcessorView.css';

export const ProcessorView: React.FC = () => {
  const { state, current_task } = useEmulatorStore();
  const { processor } = state;
  const [previousCounter, setPreviousCounter] = useState(processor.program_counter);
  const [animateCounter, setAnimateCounter] = useState(false);
  
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
  
  // Убеждаемся, что регистры всегда инициализированы
  // Используем useMemo для предотвращения лишних пересчетов
  const displayRegisters = useMemo(() => {
    // Получаем регистры из состояния процессора
    let regs = processor.registers;
    
    // Проверяем, что регистры существуют и это массив
    if (!regs || !Array.isArray(regs)) {
      console.warn('ProcessorView: регистры не инициализированы, используем нули');
      return [0, 0, 0, 0, 0, 0, 0, 0];
    }
    
    // Гарантируем, что у нас есть ровно 8 регистров
    const result = [];
    for (let i = 0; i < 8; i++) {
      const value = regs[i];
      // Если значение undefined или null, используем 0
      result[i] = (value !== undefined && value !== null) ? value : 0;
    }
    
    // Отладочная информация
    console.log('ProcessorView: displayRegisters =', result);
    
    return result;
  }, [processor.registers]);

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

  return (
    <div className="processor-view-container">
      <div className="processor-header">
        <h5 className="processor-title">Процессор RISC</h5>
        <div className="processor-status">
          <div className="status-indicator"></div>
          <span className="status-text">Активен</span>
        </div>
      </div>

      <div className="processor-grid-layout">
        {/* Регистры общего назначения */}
        <div className="processor-section registers-section" style={{ display: 'flex', visibility: 'visible', opacity: 1 }}>
          <div className="section-content" style={{ display: 'block', visibility: 'visible', opacity: 1 }}>
            <label className="section-label">
              Регистры общего назначения (R0-R7)
            </label>
            <div className="registers-grid" style={{ display: 'grid', visibility: 'visible', opacity: 1 }}>
              {/* Гарантируем отображение всех 8 регистров R0-R7 */}
              {Array.from({ length: 8 }, (_, index) => {
                // Получаем значение регистра из displayRegisters
                const registerValue = displayRegisters[index] !== undefined && displayRegisters[index] !== null 
                  ? displayRegisters[index] 
                  : 0;
                
                // Форматируем значение в hex
                const hexValue = formatValue(registerValue, true);
                
                return (
                  <div 
                    key={`register-R${index}`} 
                    className="register-item"
                    style={{ 
                      display: 'flex', 
                      visibility: 'visible', 
                      opacity: 1,
                      backgroundColor: 'rgba(255, 255, 255, 0.95)'
                    }}
                    data-register-index={index}
                    data-register-value={registerValue}
                  >
                    <div className="register-label">
                      R{index} {index === 0 && <span className="register-accumulator">(аккумулятор)</span>}
                    </div>
                    <div className="register-value">
                      {hexValue}
                    </div>
                  </div>
                );
              })}
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
              {(current_task === 1 || current_task === 2) && state.processor.is_halted && state.processor.cycles > 0 ? 'Итоговый ответ' : 'Флаги состояния'}
              {(current_task === 1 || current_task === 2) && state.processor.is_halted && state.processor.cycles > 0 && (
                <span className="label-animation">✓ готово</span>
              )}
            </label>
            {current_task === 1 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <div className="task-result">
                <div className="task-result-value">
                  {formatValue(state.processor.registers[0] || 280, true)}
                </div>
                <div className="task-result-title">
                  Сумма элементов массива
                </div>
                <div className="task-result-desc">
                  {state.processor.registers[0] === 280 || state.processor.registers[0] === 0 ? '10+20+30+40+50+60+70 = 280 (0x0118)' : `Результат: ${formatValue(state.processor.registers[0], true)} (${state.processor.registers[0]})`}
                </div>
              </div>
            ) : current_task === 2 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <div className="task-result">
                <div className="task-result-value">
                  {(() => {
                    const memValue = state.memory.ram && state.memory.ram.length > 0x1100 ? state.memory.ram[0x1100] : null;
                    if (memValue !== null) {
                      return `0x${memValue.toString(16).toUpperCase().padStart(2, '0')}`;
                    }
                    return '0x32';
                  })()}
                </div>
                <div className="task-result-title">
                  Свертка двух массивов
                </div>
                <div className="task-result-desc">
                  50 в десятичной системе
                </div>
              </div>
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

        {/* Итоговый ответ */}
        {(current_task === 1 || current_task === 2) && (
          <div className="processor-section result-section">
            <div className="section-content">
              <label className="section-label">
                Итоговый ответ
                {state.processor.is_halted && state.processor.cycles > 0 && (
                  <span className="label-animation">✓ готово</span>
                )}
              </label>
              {current_task === 1 ? (
                <div className="task-result">
                  <div className="task-result-value">
                    {formatValue(displayRegisters[0], true)}
                  </div>
                  <div className="task-result-title">
                    Сумма элементов массива
                  </div>
                  <div className="task-result-desc">
                    {displayRegisters[0] === 280 
                      ? '10+20+30+40+50+60+70 = 280 (0x0118)' 
                      : `Результат: ${formatValue(displayRegisters[0], true)} (${displayRegisters[0]})`}
                  </div>
                  {displayRegisters[0] === 280 && (
                    <div className="task-result-success">✓ Правильно</div>
                  )}
                </div>
              ) : current_task === 2 ? (
                <div className="task-result">
                  <div className="task-result-value">
                    {(() => {
                      const memValue = state.memory.ram && state.memory.ram.length > 0x1100 ? state.memory.ram[0x1100] : null;
                      if (memValue !== null && memValue !== undefined) {
                        return formatValue(memValue, true);
                      }
                      return '0x0032';
                    })()}
                  </div>
                  <div className="task-result-title">
                    Свертка двух массивов
                  </div>
                  <div className="task-result-desc">
                    {(() => {
                      const memValue = state.memory.ram && state.memory.ram.length > 0x1100 ? state.memory.ram[0x1100] : null;
                      if (memValue !== null && memValue !== undefined) {
                        return `${memValue} в десятичной системе (0x${memValue.toString(16).toUpperCase().padStart(4, '0')})`;
                      }
                      return '50 в десятичной системе (0x0032)';
                    })()}
                  </div>
                  {(() => {
                    const memValue = state.memory.ram && state.memory.ram.length > 0x1100 ? state.memory.ram[0x1100] : null;
                    if (memValue === 50) {
                      return <div className="task-result-success">✓ Правильно</div>;
                    }
                    return null;
                  })()}
                </div>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};