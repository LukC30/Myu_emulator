# instructions.py
class Instruction:
    def __init__(self, name, length, cycles):
        self.name = name
        self.length = length
        self.cycles = cycles

instructions = {
    0x00: Instruction('NOP', 1, 4), 0x10: Instruction('STOP', 2, 4), 0x76: Instruction('HALT', 1, 4),
    0xF3: Instruction('DI', 1, 4), 0xFB: Instruction('EI', 1, 4),

    # Loads com Incremento/Decremento (HL)
    0x22: Instruction('LD_(HL+)_A', 1, 8),
    0x32: Instruction('LD_(HL-)_A', 1, 8),
    0x2A: Instruction('LD_A_(HL+)', 1, 8),
    0x3A: Instruction('LD_A_(HL-)', 1, 8),

    # Loads 8-bit
    0x06: Instruction('LD_B_d8', 2, 8), 0x0E: Instruction('LD_C_d8', 2, 8), 0x16: Instruction('LD_D_d8', 2, 8),
    0x1E: Instruction('LD_E_d8', 2, 8), 0x26: Instruction('LD_H_d8', 2, 8), 0x2E: Instruction('LD_L_d8', 2, 8),
    0x3E: Instruction('LD_A_d8', 2, 8), 0x78: Instruction('LD_A_B', 1, 4), 0x79: Instruction('LD_A_C', 1, 4),
    0x0A: Instruction('LD_A_(BC)', 1, 8), 0x1A: Instruction('LD_A_(DE)', 1, 8), 0x7E: Instruction('LD_A_(HL)', 1, 8),
    0xFA: Instruction('LD_A_(a16)', 3, 16), 0x47: Instruction('LD_B_A', 1, 4), 0x4F: Instruction('LD_C_A', 1, 4),
    0x57: Instruction('LD_D_A', 1, 4), 0x5F: Instruction('LD_E_A', 1, 4), 0x67: Instruction('LD_H_A', 1, 4),
    0x6F: Instruction('LD_L_A', 1, 4), 0x02: Instruction('LD_(BC)_A', 1, 8), 0x12: Instruction('LD_(DE)_A', 1, 8),
    0x36: Instruction('LD_(HL)_d8', 2, 12),
    0x77: Instruction('LD_(HL)_A', 1, 8), 0xEA: Instruction('LD_(a16)_A', 3, 16), 0x56: Instruction('LD_D_(HL)', 1, 8),
    0x5E: Instruction('LD_E_(HL)', 1, 8), 0xE0: Instruction('LDH_(a8)_A', 2, 12), 0xF0: Instruction('LDH_A_(a8)', 2, 12),
    0xE2: Instruction('LD_(C)_A', 1, 8), 0xF2: Instruction('LD_A_(C)', 1, 8),
    0x7A: Instruction('LD_A_D', 1, 4), 
    0x7B: Instruction('LD_A_E', 1, 4), 
    0x7C: Instruction('LD_A_H', 1, 4), 
    0x7D: Instruction('LD_A_L', 1, 4), 
    0x7F: Instruction('LD_A_A', 1, 4),
    
    # Loads 16-bit
    0x01: Instruction('LD_BC_d16', 3, 12), 0x11: Instruction('LD_DE_d16', 3, 12),
    0x21: Instruction('LD_HL_d16', 3, 12), 0x31: Instruction('LD_SP_d16', 3, 12),
    
    # ALU (INC/DEC)
    0x04: Instruction('INC_B', 1, 4), 0x05: Instruction('DEC_B', 1, 4), 0x0C: Instruction('INC_C', 1, 4),
    0x0D: Instruction('DEC_C', 1, 4), 0x23: Instruction('INC_HL', 1, 8), 0x0B: Instruction('DEC_BC', 1, 8),
    
    # ALU (ADD/ADC/SUB/CP)
    0x87: Instruction('ADD_A_A', 1, 4), 0x80: Instruction('ADD_A_B', 1, 4), 0x81: Instruction('ADD_A_C', 1, 4),
    0x82: Instruction('ADD_A_D', 1, 4), 0x83: Instruction('ADD_A_E', 1, 4), 0x84: Instruction('ADD_A_H', 1, 4),
    0x85: Instruction('ADD_A_L', 1, 4), 0x86: Instruction('ADD_A_(HL)', 1, 8), 0xC6: Instruction('ADD_A_d8', 2, 8),
    
    0x8F: Instruction('ADC_A_A', 1, 4), 0x88: Instruction('ADC_A_B', 1, 4), 0x89: Instruction('ADC_A_C', 1, 4),
    0x8A: Instruction('ADC_A_D', 1, 4), 0x8B: Instruction('ADC_A_E', 1, 4), 0x8C: Instruction('ADC_A_H', 1, 4),
    0x8D: Instruction('ADC_A_L', 1, 4), 0x8E: Instruction('ADC_A_(HL)', 1, 8), 0xCE: Instruction('ADC_A_d8', 2, 8),
    
    0x90: Instruction('SUB_A_B', 1, 4), 0x91: Instruction('SUB_A_C', 1, 4), 0xD6: Instruction('SUB_A_d8', 2, 8),
    
    0xFE: Instruction('CP_d8', 2, 8), 0xBD: Instruction('CP_L', 1, 4),
    
    # Logic (AND/OR/XOR)
    0xAF: Instruction('XOR_A', 1, 4), 0xA9: Instruction('XOR_C', 1, 4), 0xA1: Instruction('AND_C', 1, 4),
    0xE6: Instruction('AND_d8', 2, 8), 0xB0: Instruction('OR_B', 1, 4), 0xB1: Instruction('OR_C', 1, 4),
    
    # 16-bit Math
    0x19: Instruction('ADD_HL_DE', 1, 8),
    
    # Shifts
    0x07: Instruction('RLCA', 1, 4), 0x17: Instruction('RLA', 1, 4), 0x2F: Instruction('CPL', 1, 4),
    
    # Stack
    0xC5: Instruction('PUSH_BC', 1, 16), 0xD5: Instruction('PUSH_DE', 1, 16), 0xE5: Instruction('PUSH_HL', 1, 16), 0xF5: Instruction('PUSH_AF', 1, 16),
    0xC1: Instruction('POP_BC', 1, 12), 0xD1: Instruction('POP_DE', 1, 12), 0xE1: Instruction('POP_HL', 1, 12), 0xF1: Instruction('POP_AF', 1, 12),
    
    # Control Flow
    0xC3: Instruction('JP_a16', 3, 16), 0xE9: Instruction('JP_(HL)', 1, 4), 0x18: Instruction('JR_r8', 2, 12), 0x20: Instruction('JR_NZ_r8', 2, 8),
    0xCD: Instruction('CALL_a16', 3, 24), 0xC9: Instruction('RET', 1, 16),
    
    # Prefix
    0xCB: Instruction('PREFIX_CB', 1, 4),

    # --- Restarts (RST) ---
    0xC7: Instruction('RST_00H', 1, 16),
    0xCF: Instruction('RST_08H', 1, 16),
    0xD7: Instruction('RST_10H', 1, 16),
    0xDF: Instruction('RST_18H', 1, 16),
    0xE7: Instruction('RST_20H', 1, 16),
    0xEF: Instruction('RST_28H', 1, 16),
    0xF7: Instruction('RST_30H', 1, 16),
    0xFF: Instruction('RST_38H', 1, 16),
}