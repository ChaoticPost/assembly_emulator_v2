export interface Task {
    id: number;
    title: string;
    description: string;
}

export interface Command {
    opcode: string;
    description: string;
}

export interface ProcessorState {
    registers: number[];           // R0-R7 регистры общего назначения
    program_counter: number;       // PC - счетчик команд
    instruction_register: number;  // IR - регистр команд
    instruction_register_asm: string; // Ассемблерное представление команды
    flags: {
        zero: boolean;      // Z - флаг нуля
        carry: boolean;     // C - флаг переноса
        overflow: boolean;  // V - флаг переполнения
        negative: boolean;  // N - флаг знака
    };
    current_command: string;
    is_halted: boolean;
    cycles: number;
}

export interface MemoryState {
    ram: number[];
    history: any[];
}

export interface EmulatorState {
    processor: ProcessorState;
    memory: MemoryState;
    source_code: string;
    machine_code: string[];
    current_task: number | null;
}

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface CompileRequest {
    source_code: string;
}

export interface ExecuteRequest {
    task_id?: number | null;
    step_by_step?: boolean;
    source_code?: string;
}

export interface TaskInfo {
    id: number;
    title: string;
    description: string;
}

export interface InstructionField {
    opcode: number;
    opcode_bits: string;
    rd: number;
    rd_bits: string;
    rs1: number;
    rs1_bits: string;
    rs2: number;
    rs2_bits: string;
    immediate: number;
    immediate_bits: string;
    addressing_mode: string;
    instruction_type: string;
}

export interface InstructionInfo {
    opcode: number;
    type: string;
    description: string;
    operands: string[];
    addressing_modes: string[];
}
