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
    const [previousRamLength, setPreviousRamLength] = useState(0);

    // Функция форматирования регистров в hex-формате для всех задач
    const formatRegisters = (registers: number[]) => {
        if (!registers || registers.length === 0) {
            // Если регистров нет, возвращаем начальное состояние
            return 'R0:0x0000, R1:0x0000, R2:0x0000, R3:0x0000, R4:0x0000, R5:0x0000, R6:0x0000, R7:0x0000';
        }

        // Гарантируем, что у нас есть ровно 8 регистров
        const regs = registers.slice(0, 8);
        while (regs.length < 8) {
            regs.push(0);
        }

        // Для всех задач отображаем в hex-формате для единообразия
        return regs.map((item, index) => {
            // Обрабатываем undefined и null
            const value = (item !== undefined && item !== null) ? item : 0;

            // Ограничиваем значение 16-битным диапазоном (0x0000 - 0xFFFF)
            // Обрабатываем как положительные, так и отрицательные числа
            const unsigned = (value >>> 0) & 0xFFFF;
            const hexString = unsigned.toString(16).toUpperCase().padStart(4, '0');
            return `R${index}:0x${hexString}`;
        }).join(', ');
    };


    // Данные для вкладки "Исполнение"
    const executionData = memory.history.map((entry, index) => {
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

        // Если регистров все еще нет, используем начальное состояние (все нули)
        if (!prevRegisters || prevRegisters.length === 0) {
            prevRegisters = [0, 0, 0, 0, 0, 0, 0, 0];
        }

        // Гарантируем, что у нас есть ровно 8 регистров
        while (prevRegisters.length < 8) {
            prevRegisters.push(0);
        }
        prevRegisters = prevRegisters.slice(0, 8);

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

        // Гарантируем, что у нас есть ровно 8 регистров
        while (currentRegisters.length < 8) {
            currentRegisters.push(0);
        }
        currentRegisters = currentRegisters.slice(0, 8);

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

        return {
            step: index + 1,
            command: commandText,
            phase: phase,
            registersBefore: formatRegisters(prevRegisters),
            registersAfter: formatRegisters(currentRegisters),
            flags: `Z=${currentFlags.zero ? 1 : 0} C=${currentFlags.carry ? 1 : 0} O=${currentFlags.overflow ? 1 : 0} N=${currentFlags.negative ? 1 : 0}`
        };
    });

    // Отслеживаем изменения для анимации
    useEffect(() => {
        if (memory.history.length > previousHistoryLength) {
            setPreviousHistoryLength(memory.history.length);
        }
    }, [memory.history.length, previousHistoryLength]);

    useEffect(() => {
        if (state.memory.ram && state.memory.ram.length > previousRamLength) {
            setPreviousRamLength(state.memory.ram.length);
        }
    }, [state.memory.ram, previousRamLength]);

    return (
        <Card title="Память" className="memory-card">
            <div className="memory-sections">
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
                        </DataTable>
                    </div>
                )}
            </div>
        </Card>
    );
};
