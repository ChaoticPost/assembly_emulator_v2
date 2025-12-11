import React, { useState, useEffect } from 'react';
import { Card } from 'primereact/card';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { useEmulatorStore } from '../../store/emulatorStore';
import './MemoryView.css';

export const MemoryView: React.FC = () => {
    const { state, current_task } = useEmulatorStore();
    const { memory } = state;
    const [previousHistoryLength, setPreviousHistoryLength] = useState(0);

    // Функция форматирования регистров в hex-формате
    // Для одноадресной архитектуры отображаем ACC, PC и IR
    const formatRegisters = (registers: number[], pc?: number, ir?: number) => {
        // Получаем ACC из массива регистров
        const accumulator = (registers && registers.length > 0 && registers[0] !== undefined && registers[0] !== null)
            ? registers[0] : 0;
        const accUnsigned = (accumulator >>> 0) & 0xFFFF;
        const accHex = accUnsigned.toString(16).toUpperCase().padStart(4, '0');

        // Получаем PC
        const pcValue = (pc !== undefined && pc !== null) ? pc : 0;
        const pcHex = pcValue.toString(16).toUpperCase().padStart(4, '0');

        // Получаем IR (опкод)
        const irValue = (ir !== undefined && ir !== null) ? ir : 0;
        const irUnsigned = (irValue >>> 0) & 0xFFFF;
        const irHex = irUnsigned.toString(16).toUpperCase().padStart(4, '0');

        // Формируем строку: ACC:0xXXXX, PC:0xXXXX, IR:0xXXXX
        return `ACC:0x${accHex}, PC:0x${pcHex}, IR:0x${irHex}`;
    };


    // Данные для вкладки "Исполнение"
    const executionData = React.useMemo(() => {
        return memory.history.map((entry, index) => {
            // Получаем регистры ДО выполнения команды
            // Приоритет: registers_before из текущей записи > registers_after из предыдущей > начальное состояние (все нули)
            let prevRegisters: number[] = [];

            // Сначала пытаемся получить registers_before из текущей записи
            if ((entry as any).registers_before && Array.isArray((entry as any).registers_before) && (entry as any).registers_before.length > 0) {
                // Преобразуем все значения в числа и создаем копию массива
                prevRegisters = (entry as any).registers_before.map((r: any) => {
                    // Обрабатываем числа и строки
                    let val: number;
                    if (typeof r === 'number') {
                        val = r;
                    } else if (typeof r === 'string') {
                        // Пытаемся распарсить как число (десятичное или hex)
                        val = r.startsWith('0x') || r.startsWith('0X') ? parseInt(r, 16) : parseInt(r, 10);
                    } else {
                        val = 0;
                    }
                    // Ограничиваем 16-битным диапазоном и проверяем на NaN
                    val = isNaN(val) ? 0 : (val & 0xFFFF);
                    return val;
                });
            } else if (index > 0) {
                // Если registers_before нет, берем registers_after из предыдущей записи
                const prevEntry = memory.history[index - 1];
                if ((prevEntry as any).registers_after && Array.isArray((prevEntry as any).registers_after) && (prevEntry as any).registers_after.length > 0) {
                    prevRegisters = (prevEntry as any).registers_after.map((r: any) => {
                        // Обрабатываем числа и строки
                        let val: number;
                        if (typeof r === 'number') {
                            val = r;
                        } else if (typeof r === 'string') {
                            // Пытаемся распарсить как число (десятичное или hex)
                            val = r.startsWith('0x') || r.startsWith('0X') ? parseInt(r, 16) : parseInt(r, 10);
                        } else {
                            val = 0;
                        }
                        // Ограничиваем 16-битным диапазоном и проверяем на NaN
                        val = isNaN(val) ? 0 : (val & 0xFFFF);
                        return val;
                    });
                } else if ((prevEntry as any).registers && Array.isArray((prevEntry as any).registers) && (prevEntry as any).registers.length > 0) {
                    prevRegisters = (prevEntry as any).registers.map((r: any) => {
                        // Обрабатываем числа и строки
                        let val: number;
                        if (typeof r === 'number') {
                            val = r;
                        } else if (typeof r === 'string') {
                            // Пытаемся распарсить как число (десятичное или hex)
                            val = r.startsWith('0x') || r.startsWith('0X') ? parseInt(r, 16) : parseInt(r, 10);
                        } else {
                            val = 0;
                        }
                        // Ограничиваем 16-битным диапазоном и проверяем на NaN
                        val = isNaN(val) ? 0 : (val & 0xFFFF);
                        return val;
                    });
                }
            }

            // Если регистров все еще нет, используем начальное состояние аккумулятора
            if (!prevRegisters || prevRegisters.length === 0) {
                prevRegisters = [0];
            }

            // Для одноадресной архитектуры используем только аккумулятор (первый элемент)
            prevRegisters = [prevRegisters[0] !== undefined ? prevRegisters[0] : 0];

            // Получаем регистры ПОСЛЕ выполнения команды
            let currentRegisters: number[] = [];

            // Сначала пытаемся получить registers_after из текущей записи
            if ((entry as any).registers_after && Array.isArray((entry as any).registers_after) && (entry as any).registers_after.length > 0) {
                // Преобразуем все значения в числа и создаем копию массива
                currentRegisters = (entry as any).registers_after.map((r: any) => {
                    // Обрабатываем числа и строки
                    let val: number;
                    if (typeof r === 'number') {
                        val = r;
                    } else if (typeof r === 'string') {
                        // Пытаемся распарсить как число (десятичное или hex)
                        val = r.startsWith('0x') || r.startsWith('0X') ? parseInt(r, 16) : parseInt(r, 10);
                    } else {
                        val = 0;
                    }
                    // Ограничиваем 16-битным диапазоном и проверяем на NaN
                    val = isNaN(val) ? 0 : (val & 0xFFFF);
                    return val;
                });
            } else if ((entry as any).registers && Array.isArray((entry as any).registers) && (entry as any).registers.length > 0) {
                currentRegisters = (entry as any).registers.map((r: any) => {
                    // Обрабатываем числа и строки
                    let val: number;
                    if (typeof r === 'number') {
                        val = r;
                    } else if (typeof r === 'string') {
                        // Пытаемся распарсить как число (десятичное или hex)
                        val = r.startsWith('0x') || r.startsWith('0X') ? parseInt(r, 16) : parseInt(r, 10);
                    } else {
                        val = 0;
                    }
                    // Ограничиваем 16-битным диапазоном и проверяем на NaN
                    val = isNaN(val) ? 0 : (val & 0xFFFF);
                    return val;
                });
            }

            // Если регистров нет, используем предыдущие (команда не изменила регистры)
            if (!currentRegisters || currentRegisters.length === 0) {
                currentRegisters = [...prevRegisters];  // Создаем копию массива
            }

            // Для одноадресной архитектуры используем только аккумулятор (первый элемент)
            currentRegisters = [currentRegisters[0] !== undefined ? currentRegisters[0] : 0];

            // Отладочная информация для первых нескольких записей
            if (index < 10) {
                console.log(`MemoryView: Step ${index + 1}`);
                console.log(`  command: ${(entry as any).command}`);
                console.log(`  entry.registers_before (raw):`, (entry as any).registers_before);
                console.log(`  entry.registers_after (raw):`, (entry as any).registers_after);
                console.log(`  entry.registers (raw):`, (entry as any).registers);
                console.log(`  prevRegisters (processed):`, prevRegisters);
                console.log(`  currentRegisters (processed):`, currentRegisters);
                console.log(`  entry (full):`, entry);
            }

            // Получаем флаги ДО выполнения команды
            let prevFlags: any = {};
            if ((entry as any).flags_before && typeof (entry as any).flags_before === 'object') {
                prevFlags = (entry as any).flags_before;
            } else if (index > 0) {
                const prevEntry = memory.history[index - 1];
                if ((prevEntry as any).flags_after && typeof (prevEntry as any).flags_after === 'object') {
                    prevFlags = (prevEntry as any).flags_after;
                } else if ((prevEntry as any).flags && typeof (prevEntry as any).flags === 'object') {
                    prevFlags = (prevEntry as any).flags;
                }
            }

            // Если флагов нет, используем начальное состояние (все false)
            if (!prevFlags || Object.keys(prevFlags).length === 0) {
                prevFlags = { zero: false, carry: false, overflow: false, negative: false };
            }

            // Получаем флаги ПОСЛЕ выполнения команды
            let currentFlags: any = {};
            if ((entry as any).flags_after && typeof (entry as any).flags_after === 'object') {
                currentFlags = (entry as any).flags_after;
            } else if ((entry as any).flags && typeof (entry as any).flags === 'object') {
                currentFlags = (entry as any).flags;
            } else {
                // Если флагов нет, используем предыдущие (команда не изменила флаги)
                currentFlags = { ...prevFlags };
            }

            // Гарантируем наличие всех флагов
            currentFlags = {
                zero: currentFlags.zero === true,
                carry: currentFlags.carry === true,
                overflow: currentFlags.overflow === true,
                negative: currentFlags.negative === true
            };

            // Пытаемся извлечь текст команды из доступных полей
            // Приоритет: command (полная строка команды) > instruction_register_asm > instruction
            let commandText = '-';
            if ((entry as any).command && typeof (entry as any).command === 'string') {
                commandText = (entry as any).command.trim();
            } else if ((entry as any).instruction_register_asm && typeof (entry as any).instruction_register_asm === 'string') {
                commandText = (entry as any).instruction_register_asm.trim();
            } else if ((entry as any).instruction && typeof (entry as any).instruction === 'string') {
                commandText = (entry as any).instruction.trim();
            }

            // Получаем фазу выполнения
            let phase = (entry as any).execution_phase || null;
            if (phase && typeof phase === 'string') {
                phase = phase.toLowerCase();
            } else {
                phase = null;
            }

            // Получаем значения RAM для отображения ИЗ ИСТОРИИ ВЫПОЛНЕНИЯ
            // Используем ram_after из записи истории, если есть, иначе ram, иначе текущее состояние
            let ramForStep: number[] | null = null;
            if ((entry as any).ram_after && Array.isArray((entry as any).ram_after)) {
                ramForStep = (entry as any).ram_after;
            } else if ((entry as any).ram && Array.isArray((entry as any).ram)) {
                ramForStep = (entry as any).ram;
            } else {
                // Fallback на текущее состояние RAM
                ramForStep = state.memory.ram && Array.isArray(state.memory.ram) ? state.memory.ram : null;
            }

            // Для задачи 1: используем историю выполнения для правильного отображения состояния на каждом шаге
            // Но гарантируем, что данные массива (0x0100-0x010F) всегда корректны из текущего состояния
            if (current_task === 1) {
                // Создаем расширенный массив RAM для отображения
                const extendedRam = ramForStep ? [...ramForStep] : [];
                // Убеждаемся, что массив достаточно длинный (до 0x0411 для переменной максимума)
                while (extendedRam.length <= 0x0411) {
                    extendedRam.push(0);
                }
                
                // Для данных массива (0x0100-0x010F) всегда используем текущее состояние RAM,
                // так как эти данные загружаются при инициализации задачи и не изменяются во время выполнения
                if (state.memory.ram && Array.isArray(state.memory.ram) && state.memory.ram.length > 0x010F) {
                    for (let addr = 0x0100; addr <= 0x010F; addr++) {
                        if (addr < state.memory.ram.length) {
                            extendedRam[addr] = state.memory.ram[addr];
                        }
                    }
                }
                
                // Для переменной максимума (0x0411) используем значение из истории выполнения,
                // если оно есть, иначе из текущего состояния RAM
                // Это позволяет видеть, как изменяется максимум на каждом шаге
                if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > 0x0411) {
                    const maxFromHistory = ramForStep[0x0411];
                    if (maxFromHistory !== undefined && maxFromHistory !== null && maxFromHistory !== 0) {
                        extendedRam[0x0411] = maxFromHistory;
                    } else if (state.memory.ram && Array.isArray(state.memory.ram) && state.memory.ram.length > 0x0411) {
                        extendedRam[0x0411] = state.memory.ram[0x0411];
                    }
                } else if (state.memory.ram && Array.isArray(state.memory.ram) && state.memory.ram.length > 0x0411) {
                    extendedRam[0x0411] = state.memory.ram[0x0411];
                }
                
                ramForStep = extendedRam;
            }

            // Получаем значение аккумулятора ACC из истории для отображения промежуточных значений
            let accumulatorValue = 0;
            if ((entry as any).registers_after && Array.isArray((entry as any).registers_after) && (entry as any).registers_after.length > 0) {
                const accVal = (entry as any).registers_after[0];
                if (accVal !== undefined && accVal !== null) {
                    accumulatorValue = typeof accVal === 'string' ? parseInt(accVal, 10) : Number(accVal);
                    if (isNaN(accumulatorValue)) accumulatorValue = 0;
                    accumulatorValue = accumulatorValue & 0xFFFF;
                }
            } else if (currentRegisters && currentRegisters.length > 0) {
                accumulatorValue = currentRegisters[0] & 0xFFFF;
            }

            let ramHexValues: string[] = [];
            let ramDecValues: string[] = [];

            if (current_task === 1) {
                // Для задачи 1 показываем элементы массива из 0x0100-0x010F
                // [0x0100] = размер массива
                // [0x0101..0x010F] = элементы массива
                // [0x0411] = переменная для сохранения текущего максимума

                // Получаем размер массива
                let arraySize = 0;
                if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > 0x0100) {
                    const sizeValue = ramForStep[0x0100];
                    if (sizeValue !== undefined && sizeValue !== null) {
                        const numSize = typeof sizeValue === 'string' ? parseInt(sizeValue, 10) : Number(sizeValue);
                        if (!isNaN(numSize) && numSize > 0 && numSize <= 15) {
                            arraySize = numSize & 0xFFFF;
                        }
                    }
                }

                // Показываем размер массива
                if (arraySize > 0) {
                    const sizeHex = arraySize.toString(16).toUpperCase().padStart(4, '0');
                    ramHexValues.push(`[0x0100]=0x${sizeHex} (размер)`);
                    ramDecValues.push(`[0x0100]=${arraySize} (размер)`);
                }

                // Отслеживаем, какие элементы уже были показаны на предыдущих шагах
                const previousElements = new Set<number>();
                if (index > 0) {
                    const prevEntry = memory.history[index - 1];
                    if (prevEntry) {
                        const prevRam = (prevEntry as any).ram_after || (prevEntry as any).ram;
                        if (prevRam && Array.isArray(prevRam)) {
                            for (let i = 1; i <= arraySize && (0x0100 + i) < prevRam.length; i++) {
                                const prevAddr = 0x0100 + i;
                                const prevValue = prevRam[prevAddr];
                                if (prevValue !== undefined && prevValue !== null && prevValue !== 0) {
                                    previousElements.add(prevAddr);
                                }
                            }
                        }
                    }
                }

                // Показываем все элементы массива, которые уже загружены (накопление)
                for (let i = 1; i <= arraySize && (0x0100 + i) <= 0x010F; i++) {
                    const addr = 0x0100 + i;
                    let value = 0;
                    let isNew = false;

                    if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > addr) {
                        const rawValue = ramForStep[addr];
                        if (rawValue !== undefined && rawValue !== null && (typeof rawValue !== 'string' || rawValue !== '')) {
                            const numValue = typeof rawValue === 'string' ? parseInt(rawValue, 10) : Number(rawValue);
                            if (!isNaN(numValue)) {
                                value = numValue & 0xFFFF;
                                // Проверяем, новый ли это элемент (не был на предыдущем шаге)
                                isNew = value !== 0 && !previousElements.has(addr);
                            }
                        }
                    }

                    const unsigned = value >>> 0;
                    // Показываем элемент, если он не равен 0
                    if (unsigned !== 0) {
                        const addrHex = addr.toString(16).toUpperCase().padStart(4, '0');
                        const valueHex = unsigned.toString(16).toUpperCase().padStart(4, '0');
                        // Формат: [0x0101]=0x000A или [0x0101]=0x000A (добавилось)
                        const newMarker = isNew ? ' ' : '';
                        ramHexValues.push(`[0x${addrHex}]=0x${valueHex}${newMarker}`);
                        ramDecValues.push(`[0x${addrHex}]=${unsigned}${newMarker}`);
                    }
                }

                // Показываем переменную максимума (адрес 0x0411 согласно примеру программы)
                // Показываем максимум всегда, когда он установлен (даже если это первый элемент массива)
                if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > 0x0411) {
                    const maxValue = ramForStep[0x0411];
                    if (maxValue !== undefined && maxValue !== null) {
                        const numMax = typeof maxValue === 'string' ? parseInt(maxValue, 10) : Number(maxValue);
                        if (!isNaN(numMax)) {
                            const maxUnsigned = (numMax >>> 0) & 0xFFFF;
                            // Показываем максимум, если он установлен (не равен 0) или если это начальный шаг
                            // На начальных шагах максимум может быть равен первому элементу массива
                            if (maxUnsigned !== 0 || index === 0) {
                                const maxHex = maxUnsigned.toString(16).toUpperCase().padStart(4, '0');
                                ramHexValues.push(`[0x0411]=0x${maxHex} (максимум)`);
                                ramDecValues.push(`[0x0411]=${maxUnsigned} (максимум)`);
                            }
                        }
                    }
                }

                // Добавляем значение аккумулятора ACC для показа текущего максимума
                const accUnsigned = accumulatorValue >>> 0;
                ramHexValues.push(`ACC:0x${accUnsigned.toString(16).toUpperCase().padStart(4, '0')}`);
                ramDecValues.push(`ACC:${accUnsigned}`);
            } else if (current_task === 2) {
                // Для задачи 2 показываем команды из RAM (архитектура фон Неймана) и данные массивов A и B
                // Команды: 0x0000-0x00FF (показываем только непустые)
                // Определяем количество команд из machine_code или истории
                const maxProgramSize = state.machine_code?.length || 50; // Максимум 50 команд для отображения
                for (let addr = 0x0000; addr < 0x0000 + maxProgramSize && addr < 0x0100; addr++) {
                    let value = 0;
                    if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > addr) {
                        const rawValue = ramForStep[addr];
                        if (rawValue !== undefined && rawValue !== null && (typeof rawValue !== 'string' || rawValue !== '')) {
                            const numValue = typeof rawValue === 'string' ? parseInt(rawValue, 10) : Number(rawValue);
                            if (!isNaN(numValue)) {
                                value = numValue & 0xFFFF;
                            }
                        }
                    }
                    const unsigned = value >>> 0;
                    // Показываем только непустые ячейки команд (значение != 0)
                    if (unsigned !== 0) {
                        // Показываем адрес и значение команды в hex формате: [0x0000]=0x1100
                        ramHexValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=0x${unsigned.toString(16).toUpperCase().padStart(4, '0')}`);
                        // Показываем адрес и значение команды в dec формате: [0x0000]=4352
                        ramDecValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=${unsigned}`);
                    }
                }

                // Массив A: 0x0200-0x020A
                for (let addr = 0x0200; addr <= 0x020A; addr++) {
                    let value = 0;
                    if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > addr) {
                        const rawValue = ramForStep[addr];
                        // Более тщательная проверка значения
                        if (rawValue !== undefined && rawValue !== null && (typeof rawValue !== 'string' || rawValue !== '')) {
                            const numValue = typeof rawValue === 'string' ? parseInt(rawValue, 10) : Number(rawValue);
                            if (!isNaN(numValue)) {
                                value = numValue & 0xFFFF;
                            }
                        }
                    }
                    const unsigned = value >>> 0;
                    // Показываем только непустые ячейки (значение != 0)
                    if (unsigned !== 0) {
                        // Показываем адрес и значение в hex формате: [0x0200]=0x000A
                        ramHexValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=0x${unsigned.toString(16).toUpperCase().padStart(4, '0')}`);
                        // Показываем адрес и значение в dec формате: [0x0200]=10
                        ramDecValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=${unsigned}`);
                    }
                }
                // Массив B: 0x0300-0x030A
                for (let addr = 0x0300; addr <= 0x030A; addr++) {
                    let value = 0;
                    if (ramForStep && Array.isArray(ramForStep) && ramForStep.length > addr) {
                        const rawValue = ramForStep[addr];
                        // Более тщательная проверка значения
                        if (rawValue !== undefined && rawValue !== null && (typeof rawValue !== 'string' || rawValue !== '')) {
                            const numValue = typeof rawValue === 'string' ? parseInt(rawValue, 10) : Number(rawValue);
                            if (!isNaN(numValue)) {
                                value = numValue & 0xFFFF;
                            }
                        }
                    }
                    const unsigned = value >>> 0;
                    // Показываем только непустые ячейки (значение != 0)
                    if (unsigned !== 0) {
                        // Показываем адрес и значение в hex формате: [0x0300]=0x000A
                        ramHexValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=0x${unsigned.toString(16).toUpperCase().padStart(4, '0')}`);
                        // Показываем адрес и значение в dec формате: [0x0300]=10
                        ramDecValues.push(`[0x${addr.toString(16).toUpperCase().padStart(4, '0')}]=${unsigned}`);
                    }
                }

                // Логируем для отладки первых нескольких шагов
                if (index < 3) {
                    console.log(`MemoryView executionData[${index}]: Проверка RAM для задачи 2`);
                    console.log(`  entry.ram_after exists:`, !!((entry as any).ram_after));
                    console.log(`  entry.ram exists:`, !!((entry as any).ram));
                    console.log(`  ramForStep length:`, ramForStep?.length || 0);
                    if (ramForStep && ramForStep.length > 0x030A) {
                        console.log(`  ramForStep[0x0200]:`, ramForStep[0x0200], `(type: ${typeof ramForStep[0x0200]})`);
                        console.log(`  ramForStep[0x0201]:`, ramForStep[0x0201], `(type: ${typeof ramForStep[0x0201]})`);
                        console.log(`  ramForStep[0x0300]:`, ramForStep[0x0300], `(type: ${typeof ramForStep[0x0300]})`);
                        console.log(`  ramForStep[0x0301]:`, ramForStep[0x0301], `(type: ${typeof ramForStep[0x0301]})`);
                    }
                }
            } else {
                // Для остальных задач показываем первые непустые значения до 0x0100
                const maxAddr = Math.min(ramForStep?.length || 0, 0x0100);
                for (let addr = 0; addr < maxAddr; addr++) {
                    const value = (ramForStep?.[addr] || 0) & 0xFFFF;
                    if (value !== 0 || ramHexValues.length < 8) {
                        const unsigned = value >>> 0;
                        ramHexValues.push(`0x${unsigned.toString(16).toUpperCase().padStart(4, '0')}`);
                        ramDecValues.push(unsigned.toString());
                        if (ramHexValues.length >= 8) break;
                    }
                }
            }

            // Извлекаем PC и IR из истории для отображения
            // PC ДО выполнения команды
            let pcBefore = 0;
            if ((entry as any).programCounter_before !== undefined && (entry as any).programCounter_before !== null) {
                pcBefore = typeof (entry as any).programCounter_before === 'string'
                    ? parseInt((entry as any).programCounter_before, 10)
                    : Number((entry as any).programCounter_before);
                if (isNaN(pcBefore)) pcBefore = 0;
            } else if ((entry as any).programCounter !== undefined && (entry as any).programCounter !== null) {
                pcBefore = typeof (entry as any).programCounter === 'string'
                    ? parseInt((entry as any).programCounter, 10)
                    : Number((entry as any).programCounter);
                if (isNaN(pcBefore)) pcBefore = 0;
            } else if (index > 0) {
                // Берем PC_after из предыдущей записи
                const prevEntry = memory.history[index - 1];
                if ((prevEntry as any).programCounter_after !== undefined && (prevEntry as any).programCounter_after !== null) {
                    pcBefore = typeof (prevEntry as any).programCounter_after === 'string'
                        ? parseInt((prevEntry as any).programCounter_after, 10)
                        : Number((prevEntry as any).programCounter_after);
                    if (isNaN(pcBefore)) pcBefore = 0;
                }
            }

            // PC ПОСЛЕ выполнения команды
            let pcAfter = pcBefore; // По умолчанию равен PC_before
            if ((entry as any).programCounter_after !== undefined && (entry as any).programCounter_after !== null) {
                pcAfter = typeof (entry as any).programCounter_after === 'string'
                    ? parseInt((entry as any).programCounter_after, 10)
                    : Number((entry as any).programCounter_after);
                if (isNaN(pcAfter)) pcAfter = pcBefore;
            } else if ((entry as any).programCounter !== undefined && (entry as any).programCounter !== null) {
                pcAfter = typeof (entry as any).programCounter === 'string'
                    ? parseInt((entry as any).programCounter, 10)
                    : Number((entry as any).programCounter);
                if (isNaN(pcAfter)) pcAfter = pcBefore;
            }

            // IR (Instruction Register) - опкод команды
            let irValue = 0;
            if ((entry as any).instruction_register !== undefined && (entry as any).instruction_register !== null) {
                irValue = typeof (entry as any).instruction_register === 'string'
                    ? parseInt((entry as any).instruction_register, 16)
                    : Number((entry as any).instruction_register);
                if (isNaN(irValue)) irValue = 0;
            }

            // IR_asm (ассемблерное представление команды) - не используется в formatRegisters, но может быть полезен для отладки
            // let irAsm = (entry as any).instruction_register_asm || commandText;

            return {
                step: index + 1,
                command: commandText,
                phase: phase,
                registersBefore: formatRegisters(prevRegisters, pcBefore, irValue),
                registersAfter: formatRegisters(currentRegisters, pcAfter, irValue),
                flags: `Z=${currentFlags.zero ? 1 : 0} C=${currentFlags.carry ? 1 : 0} O=${currentFlags.overflow ? 1 : 0} N=${currentFlags.negative ? 1 : 0}`,
                ramHex: ramHexValues.length > 0 ? ramHexValues.join(', ') : '-',
                ramDec: ramDecValues.length > 0 ? ramDecValues.join(', ') : '-'
            };
        });
    }, [
        memory.history,
        current_task,
        state.processor.registers,
        state.processor.program_counter,
        // Добавляем зависимость от RAM для задачи 1, чтобы пересчитывать при изменении памяти
        // Для задачи 1: зависимость от адресов 0x0100-0x010F и 0x0411
        current_task === 1 && state.memory.ram && state.memory.ram.length > 0x010F
            ? JSON.stringify(state.memory.ram.slice(0x0100, 0x0110))
            : null,
        current_task === 1 && state.memory.ram && state.memory.ram.length > 0x0411
            ? state.memory.ram[0x0411]
            : null,
        // Добавляем зависимость от содержимого истории для принудительного пересчета
        // Используем JSON.stringify для глубокого сравнения истории выполнения
        // Для задачи 2 нужно включить адреса до 0x030A, для задачи 1 - до 0x0108, для остальных - до 0x0200
        memory.history.length > 0 ? JSON.stringify(memory.history.map((e: any) => {
            const maxRamAddr = current_task === 2 ? 0x030A + 1 : (current_task === 1 ? 0x0110 : 0x0200);
            return {
                phase: e.execution_phase,
                ram_after: e.ram_after ? e.ram_after.slice(0, Math.min(e.ram_after.length, maxRamAddr)) : null,
                ram: e.ram ? e.ram.slice(0, Math.min(e.ram.length, maxRamAddr)) : null
            };
        })) : null,
    ]);

    // Отслеживаем изменения для анимации
    useEffect(() => {
        if (memory.history.length > previousHistoryLength) {
            setPreviousHistoryLength(memory.history.length);
        }
    }, [memory.history.length, previousHistoryLength]);

    // Логируем изменения RAM для отладки
    useEffect(() => {
        if (current_task === 1 && state.memory.ram && Array.isArray(state.memory.ram) && state.memory.ram.length > 0x010F) {
            console.log('MemoryView: RAM в компоненте обновлен');
            console.log('  ram.length:', state.memory.ram.length);
            console.log('  ram[0x0100]:', state.memory.ram[0x0100], `(type: ${typeof state.memory.ram[0x0100]})`);
            console.log('  ram[0x0105]:', state.memory.ram[0x0105], `(type: ${typeof state.memory.ram[0x0105]})`);
            if (state.memory.ram.length > 0x0411) {
                console.log('  ram[0x0411]:', state.memory.ram[0x0411], `(type: ${typeof state.memory.ram[0x0411]})`);
            }
            console.log('  ram[0x0106]:', state.memory.ram[0x0106], `(type: ${typeof state.memory.ram[0x0106]})`);
        }
    }, [state.memory.ram, current_task]);


    return (
        <Card title="Пошаговое выполнение программы" className="memory-card">
            <div className="memory-sections">
                <>
                    {current_task === 2 ? (
                        <div className="memory-section">
                            {/* Шаги выполнения для задачи 2 */}
                            <div>
                                <h4 className="mb-4">
                                    Пошаговое выполнение программы
                                    {memory.history.length > 0 && (
                                        <span className="ml-2 bg-green-100 text-green-800 text-xs font-medium px-2 py-0.5 rounded animate-pulse">
                                            Активно
                                        </span>
                                    )}
                                </h4>
                                {executionData.length > 0 ? (
                                    <DataTable
                                        value={executionData}
                                        size="small"
                                        className={`history-table ${memory.history.length > previousHistoryLength ? 'animate-slide-in-up' : ''}`}
                                        emptyMessage="Нет данных"
                                    >
                                        <Column
                                            field="step"
                                            header="ШАГ"
                                            style={{ width: '60px' }}
                                            body={(rowData) => (
                                                <span className="font-mono text-green-600 font-bold">{rowData.step}</span>
                                            )}
                                        />
                                        <Column
                                            field="phase"
                                            header="ФАЗА"
                                            style={{ width: '100px' }}
                                            body={(rowData) => {
                                                const phase = rowData.phase;
                                                if (!phase) return <span className="text-gray-400">-</span>;
                                                const phaseMap: { [key: string]: { text: string; color: string; bg: string } } = {
                                                    'fetch': { text: 'FETCH', color: 'text-blue-700', bg: 'bg-blue-100' },
                                                    'decode': { text: 'DECODE', color: 'text-yellow-700', bg: 'bg-yellow-100' },
                                                    'execute': { text: 'EXECUTE', color: 'text-green-700', bg: 'bg-green-100' }
                                                };
                                                const phaseInfo = phaseMap[phase.toLowerCase()] || { text: phase.toUpperCase(), color: 'text-gray-700', bg: 'bg-gray-100' };
                                                return (
                                                    <span className={`font-mono font-bold px-2 py-1 rounded ${phaseInfo.color} ${phaseInfo.bg}`}>
                                                        {phaseInfo.text}
                                                    </span>
                                                );
                                            }}
                                        />
                                        <Column
                                            field="command"
                                            header="КОМАНДА"
                                            body={(rowData) => (
                                                <span className="font-mono text-gray-800 bg-gray-50 px-2 py-1 rounded">{rowData.command || '-'}</span>
                                            )}
                                        />
                                        <Column
                                            field="registersBefore"
                                            header="РЕГИСТРЫ ДО"
                                            body={(rowData) => (
                                                <span className="font-mono text-orange-600">{rowData.registersBefore}</span>
                                            )}
                                        />
                                        <Column
                                            field="registersAfter"
                                            header="РЕГИСТРЫ ПОСЛЕ"
                                            body={(rowData) => (
                                                <span className="font-mono text-green-600">{rowData.registersAfter}</span>
                                            )}
                                        />
                                        <Column
                                            field="flags"
                                            header="ФЛАГИ"
                                            body={(rowData) => (
                                                <span className="font-mono text-purple-600">{rowData.flags}</span>
                                            )}
                                        />
                                        <Column
                                            field="ramHex"
                                            header="Память (hex)"
                                            style={{ width: '400px' }}
                                            body={(rowData) => (
                                                <div className="font-mono text-blue-600 text-xs whitespace-pre-wrap break-words">
                                                    {rowData.ramHex || '-'}
                                                </div>
                                            )}
                                        />
                                        <Column
                                            field="ramDec"
                                            header="Память (dec)"
                                            style={{ width: '400px' }}
                                            body={(rowData) => (
                                                <div className="font-mono text-gray-600 text-xs whitespace-pre-wrap break-words">
                                                    {rowData.ramDec || '-'}
                                                </div>
                                            )}
                                        />
                                    </DataTable>
                                ) : (
                                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                                        <div className="text-4xl mb-4">⏳</div>
                                        <h3 className="text-lg font-bold text-gray-700 mb-2">Программа не выполнена</h3>
                                        <p className="text-gray-500 mb-4">
                                            Начните выполнение программы для просмотра пошагового выполнения
                                        </p>
                                        <div className="text-sm text-gray-400">
                                            Используйте кнопки "Выполнить" или "Шаг" для запуска
                                        </div>
                                    </div>
                                )}
                            </div>


                        </div>
                    ) : (
                        <div className="memory-section">
                            <h4 className="mb-4">
                                Пошаговое выполнение программы
                                {memory.history.length > 0 && (
                                    <span className="ml-2 bg-green-100 text-green-800 text-xs font-medium px-2 py-0.5 rounded animate-pulse">
                                        Активно
                                    </span>
                                )}
                            </h4>
                            <DataTable
                                value={executionData}
                                size="small"
                                className={`history-table ${memory.history.length > previousHistoryLength ? 'animate-slide-in-up' : ''}`}
                                emptyMessage="Нет данных"
                            >
                                <Column
                                    field="step"
                                    header="ШАГ"
                                    style={{ width: '60px' }}
                                    body={(rowData) => (
                                        <span className="font-mono text-green-600 font-bold">{rowData.step}</span>
                                    )}
                                />
                                <Column
                                    field="phase"
                                    header="ФАЗА"
                                    style={{ width: '100px' }}
                                    body={(rowData) => {
                                        const phase = rowData.phase;
                                        if (!phase) return <span className="text-gray-400">-</span>;
                                        const phaseMap: { [key: string]: { text: string; color: string; bg: string } } = {
                                            'fetch': { text: 'FETCH', color: 'text-blue-700', bg: 'bg-blue-100' },
                                            'decode': { text: 'DECODE', color: 'text-yellow-700', bg: 'bg-yellow-100' },
                                            'execute': { text: 'EXECUTE', color: 'text-green-700', bg: 'bg-green-100' }
                                        };
                                        const phaseInfo = phaseMap[phase.toLowerCase()] || { text: phase.toUpperCase(), color: 'text-gray-700', bg: 'bg-gray-100' };
                                        return (
                                            <span className={`font-mono font-bold px-2 py-1 rounded ${phaseInfo.color} ${phaseInfo.bg}`}>
                                                {phaseInfo.text}
                                            </span>
                                        );
                                    }}
                                />
                                <Column
                                    field="command"
                                    header="КОМАНДА"
                                    body={(rowData) => (
                                        <span className="font-mono text-gray-800 bg-gray-50 px-2 py-1 rounded">{rowData.command || '-'}</span>
                                    )}
                                />
                                <Column
                                    field="registersBefore"
                                    header="РЕГИСТРЫ ДО"
                                    body={(rowData) => (
                                        <span className="font-mono text-orange-600">{rowData.registersBefore}</span>
                                    )}
                                />
                                <Column
                                    field="registersAfter"
                                    header="РЕГИСТРЫ ПОСЛЕ"
                                    body={(rowData) => (
                                        <span className="font-mono text-green-600">{rowData.registersAfter}</span>
                                    )}
                                />
                                <Column
                                    field="flags"
                                    header="ФЛАГИ"
                                    body={(rowData) => (
                                        <span className="font-mono text-purple-600">{rowData.flags}</span>
                                    )}
                                />
                                <Column
                                    field="ramHex"
                                    header="Значение (hex)"
                                    style={{ width: '200px' }}
                                    body={(rowData) => (
                                        <span className="font-mono text-blue-600 text-xs">{rowData.ramHex || '-'}</span>
                                    )}
                                />
                                <Column
                                    field="ramDec"
                                    header="Значение (dec)"
                                    style={{ width: '200px' }}
                                    body={(rowData) => (
                                        <span className="font-mono text-gray-600 text-xs">{rowData.ramDec || '-'}</span>
                                    )}
                                />
                            </DataTable>
                        </div>
                    )}
                </>
            </div>
        </Card>
    );
};
