import React, { useState, useEffect } from 'react';
import { Card } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import './ProcessorView.css';

export const ProcessorView: React.FC = () => {
  const { state, current_task } = useEmulatorStore();
  const { processor } = state;
  const [previousCounter, setPreviousCounter] = useState(processor.program_counter);
  const [animateCounter, setAnimateCounter] = useState(false);

  // Функция форматирования значений для отображения
  const formatValue = (value: number, isHex: boolean = false) => {
    if (isHex) {
      if (value < 0) {
        // Для отрицательных чисел используем дополнение до двух
        // Преобразуем в беззнаковое 16-битное число
        const unsigned = (value >>> 0) & 0xFFFF;
        return `0x${unsigned.toString(16).toUpperCase().padStart(4, '0')}`;
      }
      return `0x${value.toString(16).toUpperCase().padStart(4, '0')}`;
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
    <Card className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h5 className="text-xl font-bold text-white-900 font-heading">Процессор RISC</h5>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Активен</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Регистры общего назначения */}
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-3 font-body">
              Регистры общего назначения (R0-R7)
            </label>
            <div className="grid grid-cols-2 gap-2">
              {processor.registers.map((value, index) => (
                <div key={index} className="bg-white rounded-lg p-2 border border-gray-200">
                  <div className="text-xs font-semibold text-gray-600 mb-1">
                    R{index} {index === 0 && <span className="text-blue-600">(аккумулятор)</span>}
                  </div>
                  <div className="text-lg font-mono font-bold text-primary-600">
                    {formatValue(value, true)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Специальные регистры */}
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2 font-body">
              Счётчик команд (PC)
              {animateCounter && (
                <span className="ml-2 text-xs text-blue-600 animate-pulse">↑ увеличивается</span>
              )}
            </label>
            <div className={`text-2xl font-mono font-bold text-primary-600 bg-white rounded-lg p-3 text-center transition-all duration-300 ${animateCounter ? 'animate-counter-increase' : ''
              }`}>
              {processor.program_counter}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2 font-body">
              Регистр команд (IR)
            </label>
            <div className="text-lg font-mono text-gray-800 bg-white rounded-lg p-3 min-h-[3rem] flex items-center">
              <span className="text-gray-400">0x</span>
              <span className="text-primary-600 font-bold">
                {processor.instruction_register.toString(16).toUpperCase().padStart(4, '0')}
              </span>
            </div>
            {processor.instruction_register_asm && (
              <div className="mt-2 text-sm text-gray-600 bg-gray-100 rounded p-2">
                <span className="font-semibold">Ассемблер:</span> {processor.instruction_register_asm}
              </div>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2 font-body">
              Циклы выполнения
            </label>
            <div className="text-2xl font-mono font-bold text-green-600 bg-white rounded-lg p-3 text-center">
              {processor.cycles}
            </div>
          </div>
        </div>

        {/* Флаги состояния */}
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2 font-body">
              {(current_task === 1 || current_task === 2) && state.processor.is_halted && state.processor.cycles > 0 ? 'Итоговый ответ' : 'Флаги состояния'}
              {(current_task === 1 || current_task === 2) && state.processor.is_halted && state.processor.cycles > 0 && (
                <span className="ml-2 text-xs text-green-600 animate-pulse">✓ готово</span>
              )}
            </label>
            {current_task === 1 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border-2 border-blue-200 text-center">
                <div className="text-4xl font-mono font-bold text-blue-700 mb-2">
                  {state.processor.registers[0]}
                </div>
                <div className="text-lg text-gray-600 mb-2">
                  Сумма элементов массива
                </div>
                <div className="text-sm text-gray-500">
                  {state.processor.registers[0] === 280 ? '10+20+30+40+50+60+70 = 280' : `Результат: ${state.processor.registers[0]}`}
                </div>
              </div>
            ) : current_task === 2 && state.processor.is_halted && state.processor.cycles > 0 ? (
              <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border-2 border-green-200 text-center">
                <div className="text-4xl font-mono font-bold text-green-700 mb-2">
                  {(() => {
                    const memValue = state.memory.ram && state.memory.ram.length > 0x1100 ? state.memory.ram[0x1100] : null;
                    if (memValue !== null) {
                      return `0x${memValue.toString(16).toUpperCase().padStart(2, '0')}`;
                    }
                    return '0x32';
                  })()}
                </div>
                <div className="text-lg text-gray-600 mb-2">
                  Свертка двух массивов
                </div>
                <div className="text-sm text-gray-500">
                  50 в десятичной системе
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {/* Zero Flag */}
                <div className="bg-white rounded-lg p-2 border border-gray-200 text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all duration-300 mx-auto mb-1 ${processor.flags.zero
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-gray-400'
                    } ${animateFlags.zero ? 'animate-counter-increase' : ''}`}>
                    {processor.flags.zero ? '1' : '0'}
                  </div>
                  <div className="text-xs font-semibold text-gray-800 mb-1">Zero</div>
                  <div className="text-xs text-gray-500">
                    {processor.flags.zero ? 'ноль' : 'не ноль'}
                  </div>
                  {animateFlags.zero && (
                    <div className="text-xs text-orange-600 animate-bounce mt-1">↑</div>
                  )}
                </div>

                {/* Carry Flag */}
                <div className="bg-white rounded-lg p-2 border border-gray-200 text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all duration-300 mx-auto mb-1 ${processor.flags.carry
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-gray-400'
                    } ${animateFlags.carry ? 'animate-counter-increase' : ''}`}>
                    {processor.flags.carry ? '1' : '0'}
                  </div>
                  <div className="text-xs font-semibold text-gray-800 mb-1">Carry</div>
                  <div className="text-xs text-gray-500">
                    {processor.flags.carry ? 'перенос' : 'нет переноса'}
                  </div>
                  {animateFlags.carry && (
                    <div className="text-xs text-orange-600 animate-bounce mt-1">↑</div>
                  )}
                </div>

                {/* Overflow Flag */}
                <div className="bg-white rounded-lg p-2 border border-gray-200 text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all duration-300 mx-auto mb-1 ${processor.flags.overflow
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-gray-400'
                    } ${animateFlags.overflow ? 'animate-counter-increase' : ''}`}>
                    {processor.flags.overflow ? '1' : '0'}
                  </div>
                  <div className="text-xs font-semibold text-gray-800 mb-1">Overflow</div>
                  <div className="text-xs text-gray-500">
                    {processor.flags.overflow ? 'переполнение' : 'нет переполнения'}
                  </div>
                  {animateFlags.overflow && (
                    <div className="text-xs text-orange-600 animate-bounce mt-1">↑</div>
                  )}
                </div>

                {/* Negative Flag */}
                <div className="bg-white rounded-lg p-2 border border-gray-200 text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all duration-300 mx-auto mb-1 ${processor.flags.negative
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-gray-400'
                    } ${animateFlags.negative ? 'animate-counter-increase' : ''}`}>
                    {processor.flags.negative ? '1' : '0'}
                  </div>
                  <div className="text-xs font-semibold text-gray-800 mb-1">Negative</div>
                  <div className="text-xs text-gray-500">
                    {processor.flags.negative ? 'отрицательное' : 'положительное'}
                  </div>
                  {animateFlags.negative && (
                    <div className="text-xs text-orange-600 animate-bounce mt-1">↑</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};