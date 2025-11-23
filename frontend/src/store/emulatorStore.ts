import { create } from 'zustand';
import type { EmulatorState, TaskInfo } from '../types/emulator';
import { apiService } from '../services/api';

const initialState: EmulatorState = {
    processor: {
        registers: [0, 0, 0, 0, 0, 0, 0, 0],  // R0-R7
        program_counter: 0,
        instruction_register: 0,
        instruction_register_asm: '',
        flags: {
            zero: false,
            carry: false,
            overflow: false,
            negative: false,
        },
        current_command: '',
        is_halted: false,
        cycles: 0,
    },
    memory: {
        ram: [],
        history: [],
    },
    source_code: '',
    machine_code: [],
    current_task: null,
};

export const useEmulatorStore = create<{
    state: EmulatorState;
    tasks: TaskInfo[];
    loading: boolean;
    error: string | null;
    current_task: number | null;
    setSourceCode: (code: string) => void;
    setCurrentTask: (taskId: number | null) => void;
    loadState: () => Promise<void>;
    loadTasks: () => Promise<void>;
    compileCode: (code: string) => Promise<void>;
    executeCode: (taskId?: number) => Promise<void>;
    executeStep: () => Promise<void>;
    executeRemaining: () => Promise<void>;
    reset: () => Promise<void>;
    setState: (newState: EmulatorState) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    loadTask1Data: () => Promise<void>;
    loadTask2Data: () => Promise<void>;
}>((set, get) => ({
    state: initialState,
    tasks: [],
    loading: false,
    error: null,
    current_task: null,

    setSourceCode: (code) => set((state) => ({
        state: { ...state.state, source_code: code }
    })),

    setCurrentTask: async (taskId) => {
        console.log('[setCurrentTask] Устанавливаем задачу:', taskId);
        // ВАЖНО: сначала устанавливаем current_task, чтобы он был доступен сразу
        set((state) => ({
            state: { ...state.state, current_task: taskId },
            current_task: taskId
        }));

        // Если выбрана задача, загружаем её данные
        if (taskId) {
            try {
                console.log('[setCurrentTask] Загружаем данные задачи', taskId);
                const result = await apiService.loadTask(taskId);
                if (result.success) {
                    // ВАЖНО: сохраняем current_task при обновлении состояния
                    set({ 
                        state: { ...result.state, current_task: taskId },
                        current_task: taskId
                    });
                    console.log('[setCurrentTask] Данные задачи загружены, current_task сохранен:', taskId);
                }
            } catch (error) {
                console.warn('[setCurrentTask] Не удалось загрузить данные задачи:', error);
            }
        }
    },

    setState: (newState) => set({ state: newState }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error }),

    loadTask1Data: async () => {
        try {
            set({ loading: true, error: null });
            console.log('Загружаем данные для задачи 1');
            const result = await apiService.loadTask(1);
            if (result.success) {
                set({
                    state: result.state,
                    current_task: 1,
                    loading: false
                });
                console.log('Данные задачи 1 загружены:', result.state);
            } else {
                set({ error: 'Ошибка загрузки данных задачи 1', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка загрузки данных задачи 1',
                loading: false
            });
        }
    },

    loadTask2Data: async () => {
        try {
            set({ loading: true, error: null });
            console.log('Загружаем данные для задачи 2');
            const result = await apiService.loadTask(2);
            if (result.success) {
                set({
                    state: result.state,
                    current_task: 2,
                    loading: false
                });
                console.log('Данные задачи 2 загружены:', result.state);
            } else {
                set({ error: 'Ошибка загрузки данных задачи 2', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка загрузки данных задачи 2',
                loading: false
            });
        }
    },

    loadState: async () => {
        try {
            set({ loading: true, error: null });
            const state = await apiService.getState();
            set({ state, loading: false });
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка загрузки состояния',
                loading: false
            });
        }
    },

    loadTasks: async () => {
        try {
            set({ loading: true, error: null });
            const tasks = await apiService.getTasks();
            set({ tasks, loading: false });
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка загрузки задач',
                loading: false
            });
        }
    },

    compileCode: async (code: string) => {
        try {
            set({ loading: true, error: null });
            
            // Если выбрана задача, автоматически загружаем данные задачи перед компиляцией
            const currentState = get();
            const current_task = currentState.current_task;
            const state_current_task = currentState.state.current_task;
            
            console.log('=== COMPILE CODE START ===');
            console.log('current_task from store:', current_task);
            console.log('state.current_task:', state_current_task);
            console.log('memory.ram.length:', currentState.state.memory.ram.length);
            console.log('memory.ram[0x0100]:', currentState.state.memory.ram[0x0100]);
            
            let taskState: EmulatorState | null = null;
            
            // Используем current_task из store или из state
            // ВАЖНО: проверяем оба места и убеждаемся, что taskId не null/undefined
            let taskId: number | undefined = undefined;
            if (current_task !== null && current_task !== undefined) {
                taskId = current_task;
            } else if (state_current_task !== null && state_current_task !== undefined) {
                taskId = state_current_task;
            }
            
            console.log('[COMPILE] taskId для передачи в компиляцию:', taskId);
            console.log('[COMPILE] current_task from store:', current_task);
            console.log('[COMPILE] state.current_task:', state_current_task);
            console.log('[COMPILE] taskId после проверки:', taskId);
            
            // НЕ загружаем задачу на фронтенде - пусть бэкенд сделает это
            // Это гарантирует, что данные загружаются в правильном порядке
            
            console.log('[COMPILE] Отправляем запрос на компиляцию с task_id:', taskId);
            // Передаем task_id в запрос компиляции, чтобы бэкенд загрузил данные задачи
            // ВАЖНО: передаем taskId только если он определен (не null и не undefined)
            const result = await apiService.compileCode(code, taskId);
            console.log('[COMPILE] Результат компиляции:', result);
            
            if (result.success) {
                // Если бэкенд вернул состояние, используем его (включая память)
                if ((result as any).state) {
                    const backendState = (result as any).state;
                    console.log('[COMPILE] Получено состояние с бэкенда после компиляции');
                    console.log('[COMPILE] memory.ram.length:', backendState.memory?.ram?.length);
                    console.log('[COMPILE] memory.ram[0x0100]:', backendState.memory?.ram?.[0x0100] ?? 'не найдено');
                    set({
                        state: {
                            ...backendState,
                            source_code: code,
                            machine_code: result.machine_code,
                            current_task: taskId || backendState.current_task
                        },
                        current_task: taskId || backendState.current_task,
                        loading: false
                    });
                } else {
                    // Если состояния нет, используем локальное
                    console.log('[COMPILE] Состояние с бэкенда не получено, используем локальное');
                    set((state) => {
                        const newState = taskState ? {
                            ...taskState,
                            source_code: code,
                            machine_code: result.machine_code,
                            current_task: taskId || taskState.current_task
                        } : {
                            ...state.state,
                            source_code: code,
                            machine_code: result.machine_code
                        };
                        console.log('[COMPILE] Новое состояние:', newState);
                        console.log('[COMPILE] memory.ram[0x0100]:', newState.memory.ram[0x0100]);
                        return {
                            state: newState,
                            current_task: taskId || newState.current_task,
                            loading: false
                        };
                    });
                }
                console.log('=== COMPILE CODE END ===');
            } else {
                console.error('[COMPILE] Ошибка компиляции:', result);
                set({ error: 'Ошибка компиляции', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка компиляции',
                loading: false
            });
        }
    },

    executeCode: async (taskId?: number) => {
        try {
            set({ loading: true, error: null });

            // Если taskId не указан, используем текущий исходный код
            const request = taskId
                ? { task_id: taskId, step_by_step: false }
                : { task_id: null, step_by_step: false, source_code: get().state.source_code };

            const result = await apiService.executeCode(request);
            if (result.success) {
                set({ state: result.state, loading: false });
            } else {
                set({ error: 'Ошибка выполнения', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка выполнения',
                loading: false
            });
        }
    },

    executeStep: async () => {
        try {
            set({ loading: true, error: null });

            // Если выбрана задача, но данные не загружены, загружаем их
            const state = get().state;
            const current_task = get().current_task;
            if (current_task && state.memory.ram.length === 0) {
                console.log('Загружаем данные задачи', current_task);
                const result = await apiService.loadTask(current_task);
                if (result.success) {
                    set({ state: result.state, loading: false });
                    return;
                }
            }

            const result = await apiService.executeStep();
            if (result.success) {
                set({ state: result.state, loading: false });
                console.log('Шаг выполнен:', result.state);
            } else {
                set({ error: 'Ошибка выполнения шага', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка выполнения шага',
                loading: false
            });
        }
    },

    executeRemaining: async () => {
        try {
            set({ loading: true, error: null });

            // Если выбрана задача, но данные не загружены, загружаем их
            const state = get().state;
            const current_task = get().current_task;
            if (current_task && state.memory.ram.length === 0) {
                console.log('Загружаем данные задачи', current_task);
                const result = await apiService.loadTask(current_task);
                if (result.success) {
                    set({ state: result.state, loading: false });
                    return;
                }
            }

            console.log('Выполняем оставшиеся команды...');

            let stepCount = 0;
            const maxSteps = 1000; // Защита от бесконечного цикла
            let lastState = null;

            while (stepCount < maxSteps) {
                const result = await apiService.executeStep();

                if (!result.success) {
                    set({ error: 'Ошибка выполнения команды', loading: false });
                    return;
                }

                stepCount++;
                lastState = result.state;
                console.log(`Шаг ${stepCount}: Счетчик ${result.state.processor.program_counter}, Регистры ${result.state.processor.registers}`);

                // Если программа остановлена, выходим из цикла
                if (result.state.processor.is_halted) {
                    console.log('Программа остановлена');
                    break;
                }

                // Если больше нет команд для выполнения
                if (!result.continues) {
                    console.log('Нет больше команд для выполнения');
                    break;
                }

                // Быстрое выполнение без задержки для лучшей производительности
                // await new Promise(resolve => setTimeout(resolve, 50));
            }

            // Обновляем финальное состояние
            if (lastState) {
                set({ state: lastState, loading: false });
            } else {
                set({ loading: false });
            }

            console.log(`Выполнено ${stepCount} шагов. Финальный результат:`, lastState);

        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка выполнения оставшихся команд',
                loading: false
            });
        }
    },

    reset: async () => {
        try {
            set({ loading: true, error: null });
            const result = await apiService.reset();
            if (result.success) {
                set({
                    state: result.state,
                    loading: false,
                    error: null
                });
                console.log('Процессор сброшен:', result.state);
            } else {
                set({ error: 'Ошибка сброса', loading: false });
            }
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Ошибка сброса',
                loading: false
            });
        }
    },
}));
