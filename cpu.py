from mmu import MMU
# from utils import _print # Logs desligados para performance
from instruction_set import instructions

FLAG_Z = 0x80
FLAG_N = 0x40
FLAG_H = 0x20
FLAG_C = 0x10

class CPU:
    def __init__(self, mmu: MMU):
        print("CPU Blindada inicializada")
        self.mmu = mmu

        self.A = 0x01
        self.F = 0xB0
        self.B = 0x00
        self.C = 0x13
        self.D = 0x00
        self.E = 0xD8
        self.H = 0x01
        self.L = 0x4D

        self.SP = 0xFFFE
        self.PC = 0x0100
        
        self.ime = False

    def step(self):
        self.handle_interrupts()
        
        # BLINDAGEM 1: Garante que PC esteja sempre dentro de 16-bits
        self.PC &= 0xFFFF
        
        opcode = self.mmu.read_byte(self.PC)

        if opcode not in instructions:
            # Em vez de fechar o emulador, pulamos a instrução inválida
            # Isso evita fechar a janela em caso de bugs menores
            self.PC = (self.PC + 1) & 0xFFFF
            return 4 

        instr = instructions[opcode]
        self.PC = (self.PC + 1) & 0xFFFF # Incremento seguro

        if instr.name == "LD_HL_SP+r8":
            parts = instr.name.split('_')
            self.op_LD_HL_SP(instr, parts)
            return instr.cycles
        
        # Dispatch Otimizado
        op_name = instr.name
        idx = op_name.find('_')
        if idx != -1:
            operation = op_name[:idx]
            parts = op_name.split('_')
        else:
            operation = op_name
            parts = [op_name]

        method = getattr(self, f'op_{operation}', None)

        if method:
            method(instr, parts)
        else:
            # print(f"Aviso: Handler não implementado para {instr.name}")
            pass

        return instr.cycles

    
    def get_operand_value(self, operand_str):
        match operand_str:
            case 'A': return self.A
            case 'B': return self.B
            case 'C': return self.C
            case 'D': return self.D
            case 'E': return self.E
            case 'H': return self.H
            case 'L': return self.L

            case 'AF': return (self.A << 8) | self.F
            case 'BC': return (self.B << 8) | self.C
            case 'DE': return (self.D << 8) | self.E
            case 'HL': return (self.H << 8) | self.L
            case 'SP': return self.SP

            case 'd8' | 'a8' | 'r8':
                val = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                return val
            
            case 'd16' | 'a16':
                low = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                high = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                return (high << 8) | low
            
            case '(BC)': return self.mmu.read_byte((self.B << 8) | self.C)
            case '(DE)': return self.mmu.read_byte((self.D << 8) | self.E)
            case '(HL)': return self.mmu.read_byte((self.H << 8) | self.L)

            case '(HL+)':
                hl = (self.H << 8) | self.L
                val = self.mmu.read_byte(hl)
                hl = (hl + 1) & 0xFFFF
                self.H = (hl >> 8) & 0xFF
                self.L = hl & 0xFF
                return val
            
            case '(HL-)':
                hl = (self.H << 8) | self.L
                val = self.mmu.read_byte(hl)
                hl = (hl - 1) & 0xFFFF
                self.H = (hl >> 8) & 0xFF
                self.L = hl & 0xFF
                return val

            case '(C)': return self.mmu.read_byte(0xFF00 + self.C)
            
            case '(a16)':
                low = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                high = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                addr = (high << 8) | low
                return self.mmu.read_byte(addr)
        
            case _:
                return 0

    def set_operand_value(self, dest, value):
        match dest:    
            case 'A':  self.A = value
            case 'B':  self.B = value
            case 'C':  self.C = value
            case 'D':  self.D = value
            case 'E':  self.E = value
            case 'H':  self.H = value
            case 'L':  self.L = value

            case 'HL':
                self.H = (value >> 8) & 0xFF
                self.L = value & 0xFF
            case 'BC':
                self.B = (value >> 8) & 0xFF
                self.C = value & 0xFF
            case 'DE':
                self.D = (value >> 8) & 0xFF
                self.E = value & 0xFF
            case 'SP':
                self.SP = value & 0xFFFF # BLINDAGEM SP

            case 'AF':
                self.A = (value >> 8) & 0xFF
                self.F = value & 0xF0 

            case '(BC)': self.mmu.write_byte((self.B << 8) | self.C, value)
            case '(DE)': self.mmu.write_byte((self.D << 8) | self.E, value)
            case '(HL)': self.mmu.write_byte((self.H << 8) | self.L, value)

            case '(HL+)':
                hl = (self.H << 8) | self.L
                self.mmu.write_byte(hl, value)
                hl = (hl + 1) & 0xFFFF
                self.H = (hl >> 8) & 0xFF
                self.L = hl & 0xFF
                
            case '(HL-)':
                hl = (self.H << 8) | self.L
                self.mmu.write_byte(hl, value)
                hl = (hl - 1) & 0xFFFF
                self.H = (hl >> 8) & 0xFF
                self.L = hl & 0xFF
            
            case '(C)': self.mmu.write_byte(0xFF00 + self.C, value)
            
            case '(a16)':
                low = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                high = self.mmu.read_byte(self.PC)
                self.PC = (self.PC + 1) & 0xFFFF
                addr = (high << 8) | low
                self.mmu.write_byte(addr, value)
    
    def handle_interrupts(self):
        if not self.ime:
            return

        ie = self.mmu.read_byte(0xFFFF)
        if_flag = self.mmu.read_byte(0xFF0F)
        fired = ie & if_flag

        if fired > 0:
            if fired & 0x01: self.service_interrupt(0, 0x0040)
            elif fired & 0x02: self.service_interrupt(1, 0x0048)
            elif fired & 0x04: self.service_interrupt(2, 0x0050)
            elif fired & 0x08: self.service_interrupt(3, 0x0058)
            elif fired & 0x10: self.service_interrupt(4, 0x0060)

    def service_interrupt(self, bit_n, vector):
        self.ime = False
        if_flag = self.mmu.read_byte(0xFF0F)
        if_flag &= ~(1 << bit_n)
        self.mmu.write_byte(0xFF0F, if_flag)

        # BLINDAGEM NA STACK
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, self.PC & 0xFF)

        self.PC = vector

    def alu_add(self, value, carry=False):
        c_val = 1 if (carry and (self.F & FLAG_C)) else 0
        result = self.A + value + c_val
        
        self.F = 0
        if (result & 0xFF) == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) + (value & 0x0F) + c_val > 0x0F: self.F |= FLAG_H
        if result > 0xFF: self.F |= FLAG_C
        
        self.A = result & 0xFF

    def add_16_bit(self, source):
        hl = (self.H << 8) | self.L
        value = self.get_operand_value(source)
        result = hl + value

        self.F &= ~FLAG_N
        if (hl & 0x0FFF) + (value & 0x0FFF) > 0x0FFF: self.F |= FLAG_H
        else: self.F &= ~FLAG_H
        if result > 0xFFFF: self.F |= FLAG_C
        else: self.F &= ~FLAG_C

        result &= 0xFFFF
        self.H = (result >> 8) & 0xFF
        self.L = result & 0xFF


    def op_NOP(self, inst, parts):
        pass

    def op_ADD(self, inst, parts):   
        target = parts[1]
        source = parts[2]

        match target: 
            case 'HL':
                self.add_16_bit(source)
                return
            
            case 'SP':
                offset = self.get_operand_value(source)
                if offset > 127: offset -= 256
                sp_val = self.SP

                self.F = 0
                if(sp_val & 0x0F) + (offset & 0x0F) > 0x0F: self.F |= FLAG_H
                if(sp_val & 0xFF) + (offset & 0xFF) > 0xFF: self.F |= FLAG_C

                self.SP = (self.SP + offset) & 0xFFFF
                return

        val = self.get_operand_value(source)
        self.alu_add(val, carry=False)
    
    def op_ADC(self, inst, parts):
        source = parts[2]
        val = self.get_operand_value(source)
        self.alu_add(val, carry=True)

    def op_LD(self, inst, parts):
        dest_str = parts[1]
        src = parts[2]

        if dest_str == "(a16)" and src == 'SP':
            addr = self.get_operand_value('a16')

            self.mmu.write_byte(addr, self.SP & 0xFF)
            self.mmu.write_byte((addr + 1) & 0xFFFF, (self.SP >> 8) & 0xFF)

            return

        if dest_str == 'HL' and src == 'SP+r8':
            offset = self.get_operand_value('r8')
            if offset > 127: offset -= 256

            sp_val = self.SP
            result = (sp_val + offset) & 0xFFFF

            self.F = 0
            if(sp_val&0x0F)+(offset&0x0F)>0x0F: self.F |= FLAG_H
            if(sp_val&0xFF)+(offset&0xFF)>0xFF: self.F |= FLAG_C

            self.H = (result >> 8) & 0xFF
            self.L = result & 0xFF
            return
            
        value = self.get_operand_value(src)
        self.set_operand_value(dest_str, value)

    def op_INC(self, inst, parts):
        target = parts[1]
        
        # 16 Bits (com blindagem)
        if target in ['BC', 'DE', 'HL', 'SP']:
            val = self.get_operand_value(target)
            val = (val + 1) & 0xFFFF
            self.set_operand_value(target, val)
            return

        # 8 Bits
        val = self.get_operand_value(target)
        result = (val + 1) & 0xFF
        self.set_operand_value(target, result)

        self.F &= ~FLAG_N
        if result == 0: self.F |= FLAG_Z
        else: self.F &= ~FLAG_Z
        
        if (val & 0x0F) + 1 > 0x0F: self.F |= FLAG_H
        else: self.F &= ~FLAG_H

    def op_DEC(self, inst, parts):
        target = parts[1]
        
        # 16 Bits (com blindagem)
        if target in ['BC', 'DE', 'HL', 'SP']:
            val = self.get_operand_value(target)
            val = (val - 1) & 0xFFFF
            self.set_operand_value(target, val)
            return

        # 8 Bits
        val = self.get_operand_value(target)
        result = (val - 1) & 0xFF
        self.set_operand_value(target, result)

        self.F |= FLAG_N
        if result == 0: self.F |= FLAG_Z
        else: self.F &= ~FLAG_Z

        if (val & 0x0F) == 0: self.F |= FLAG_H
        else: self.F &= ~FLAG_H

    def op_AND(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A &= val
        self.update_logic_flags(h=True)

    def op_OR(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A |= val
        self.update_logic_flags(h=False)

    def op_XOR(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A ^= val
        self.update_logic_flags(h=False)

    def op_CP(self, inst, parts):
        val = self.get_operand_value(parts[1])
        res = self.A - val
        self.F = FLAG_N
        if res == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) < (val & 0x0F): self.F |= FLAG_H
        if self.A < val: self.F |= FLAG_C

    def update_logic_flags(self, h):
        self.F = 0
        if self.A == 0: self.F |= FLAG_Z
        if h: self.F |= FLAG_H

    def op_PUSH(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, (val >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, val & 0xFF)

    def op_POP(self, inst, parts):
        low = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        high = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        val = (high << 8) | low
        
        target = parts[1]
        if target == 'AF':
            val &= 0xFFF0
        
        self.set_operand_value(target, val)

    def op_JP(self, inst, parts):
        if len(parts) > 2: 
            cond = parts[1]
            dest = self.get_operand_value(parts[2]) 
            if self.check_condition(cond):
                self.PC = dest
        else: 
            operand = parts[1]
            if operand == '(HL)':
                self.PC = (self.H << 8) | self.L
            else:
                dest = self.get_operand_value(operand)
                self.PC = dest

    def op_JR(self, inst, parts):
        jump = True
        
        if len(parts) > 2:
            cond = parts[1]
            if not self.check_condition(cond):
                jump = False
            raw_offset = self.get_operand_value(parts[2])
        else:
            raw_offset = self.get_operand_value(parts[1])

        if raw_offset > 127: raw_offset -= 256
        
        if jump:
            self.PC = (self.PC + raw_offset) & 0xFFFF # BLINDAGEM DE JUMP

    def op_CALL(self, inst, parts):
        dest = 0
        should_call = True
        
        if len(parts) > 2:
            dest = self.get_operand_value(parts[2])
            if not self.check_condition(parts[1]):
                should_call = False
        else:
            dest = self.get_operand_value(parts[1])
            
        if should_call:
            self.SP = (self.SP - 1) & 0xFFFF
            self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)
            self.SP = (self.SP - 1) & 0xFFFF
            self.mmu.write_byte(self.SP, self.PC & 0xFF)
            self.PC = dest

    def op_RET(self, inst, parts):
        if len(parts) > 1:
            if not self.check_condition(parts[1]):
                return

        low = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        high = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        self.PC = (high << 8) | low

    def check_condition(self, cond):
        if cond == 'NZ': return not (self.F & FLAG_Z)
        if cond == 'Z': return (self.F & FLAG_Z)
        if cond == 'NC': return not (self.F & FLAG_C)
        if cond == 'C': return (self.F & FLAG_C)
        return False
    
    def op_DI(self, inst, parts): self.ime = False
    def op_EI(self, inst, parts): self.ime = True
    def op_HALT(self, inst, parts): pass
    def op_STOP(self, inst, parts): pass
    
    def op_RLCA(self, inst, parts):
        bit7 = (self.A >> 7) & 1
        self.A = ((self.A << 1) | bit7) & 0xFF
        self.F = FLAG_C if bit7 else 0
        
    def op_RLA(self, inst, parts):
        bit7 = (self.A >> 7) & 1
        carry = 1 if (self.F & FLAG_C) else 0
        self.A = ((self.A << 1) | carry) & 0xFF
        self.F = FLAG_C if bit7 else 0
        
    def op_CPL(self, inst, parts):
        self.A = (~self.A) & 0xFF
        self.F |= (FLAG_N | FLAG_H)

    def op_SUB(self, inst, parts):
        val = self.get_operand_value(parts[2])
        result = self.A - val
        self.F = FLAG_N
        if result == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) < (val & 0x0F): self.F |= FLAG_H
        if self.A < val: self.F |= FLAG_C
        self.A = result & 0xFF

    def op_RETI(self, inst, parts):
        low = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        high = self.mmu.read_byte(self.SP)
        self.SP = (self.SP + 1) & 0xFFFF
        self.PC = (high << 8) | low
        self.ime = True
    
    def op_RST(self, inst, parts):
        dest_str = parts[1].replace('H', '')
        dest = int(dest_str, 16)
        
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFFFF
        self.mmu.write_byte(self.SP, self.PC & 0xFF)
        
        self.PC = dest
    
    def op_LDH(self, inst, parts):
        dest = parts[1]
        src = parts[2]

        if dest == '(a8)':
            offset = self.get_operand_value('a8')
            address = 0xFF00 + offset
            val = self.get_operand_value(src)
            self.mmu.write_byte(address, val)

        elif src == '(a8)':
            offset = self.get_operand_value('a8')
            address = 0xFF00 + offset
            val = self.mmu.read_byte(address)
            self.set_operand_value(dest, val)

    def op_PREFIX(self, inst, parts):
        cb_opcode = self.mmu.read_byte(self.PC)
        self.PC = (self.PC + 1) & 0xFFFF # avança e protege o PC

        reg_id = cb_opcode & 0x07
        bit = (cb_opcode >> 3) & 0x07
        operation = (cb_opcode >> 6) & 0x03
        
        reg_map = {0: 'B', 1: 'C', 2: 'D', 3: 'E', 4: 'H', 5: 'L', 6: '(HL)', 7: 'A'}
        operand_str = reg_map[reg_id]

        if operation == 1: 
            val = self.get_operand_value(operand_str)
            is_set = (val >> bit) & 1
            if is_set == 0: self.F |= FLAG_Z
            else: self.F &= ~FLAG_Z
            self.F &= ~FLAG_N 
            self.F |= FLAG_H  
            
        elif operation == 2:
            val = self.get_operand_value(operand_str)
            result = val & ~(1 << bit)
            self.set_operand_value(operand_str, result)
            
        elif operation == 3:
            val = self.get_operand_value(operand_str)
            result = val | (1 << bit)
            self.set_operand_value(operand_str, result)
            
        elif operation == 0:
            rot_type = (cb_opcode >> 3) & 0x07
            val = self.get_operand_value(operand_str)
            result = 0
            
            carry_flag = 1 if (self.F & FLAG_C) else 0
            bit7 = (val >> 7) & 1
            bit0 = val & 1

            match rot_type:
                case 0:
                    result = ((val << 1) | bit7) & 0xFF
                    self.F = FLAG_C if bit7 else 0

                case 1:
                    result = ((val >> 1) | (bit0 << 7)) & 0xFF
                    self.F = FLAG_C if bit0 else 0

                case 2:
                    result = ((val << 1) | carry_flag) & 0xFF
                    self.F = FLAG_C if bit7 else 0

                case 3:
                    result = ((val >> 1) | (carry_flag << 7)) & 0xFF
                    self.F = FLAG_C if bit0 else 0

                case 4:
                    result = (val << 1) & 0xFF
                    self.F = FLAG_C if bit7 else 0

                case 5:
                    result = (val >> 1) | (val & 0x80)
                    self.F = FLAG_C if bit0 else 0

                case 6:
                    result = ((val & 0xF0) >> 4) | ((val & 0x0F) << 4)
                    self.F = 0

                case 7:
                    result = (val >> 1)
                    self.F = FLAG_C if bit0 else 0

            if result == 0: self.F |= FLAG_Z
            self.F &= ~(FLAG_N | FLAG_H)
            self.set_operand_value(operand_str, result)

    def increment_hl(self):
        val = ((self.H << 8) | self.L) + 1
        val &= 0xFFFF
        self.H = (val >> 8) & 0xFF
        self.L = val & 0xFF

    def decrement_hl(self):
        val = ((self.H << 8) | self.L) - 1
        val &= 0xFFFF
        self.H = (val >> 8) & 0xFF
        self.L = val & 0xFF


    def op_RRCA(self, inst, parts):
        bit0 = self.A & 1
        self.A = ((self.A >> 1) | (bit0 << 7)) & 0xFF
        self.F = FLAG_C if bit0 else 0
        
    def op_RRA(self, inst, parts):
        bit0 = self.A & 1
        carry = 1 if (self.F & FLAG_C) else 0
        self.A = ((self.A >> 1) | (carry << 7)) & 0xFF
        self.F = FLAG_C if bit0 else 0

    def op_SCF(self, inst, parts):
        self.F &= ~(FLAG_N | FLAG_H) 
        self.F |= FLAG_C             

    def op_CCF(self, inst, parts):
        self.F &= ~(FLAG_N | FLAG_H) 
        self.F ^= FLAG_C             

    def op_SBC(self, inst, parts):
        val = self.get_operand_value(parts[2]) 
        carry = 1 if (self.F & FLAG_C) else 0
        result = self.A - val - carry
        
        self.F = FLAG_N
        if (result & 0xFF) == 0: self.F |= FLAG_Z
        
        if (self.A & 0x0F) < (val & 0x0F) + carry: self.F |= FLAG_H
        
        if result < 0: self.F |= FLAG_C
        
        self.A = result & 0xFF

    def op_DAA(self, inst, parts):

        a = self.A

        if not (self.F & FLAG_N):
            if(self.F & FLAG_H) or (a > 0x0F) > 9:
                a += 0x06
            if(self.F & FLAG_C) or (a > 0x9F):
                a += 0x60
                self.F |= FLAG_C
        else:
            if(self.F & FLAG_H):
                a -= 0x06
            if(self.F & FLAG_C):
                a -= 0x60
        self.A = a & 0xFF

        if self.A == 0: self.F |= FLAG_Z
        else: self.F &= ~FLAG_Z

        self.F &= ~FLAG_H

    def op_LD_HL_SP (self, inst, parts):

        offset = self.get_operand_value('r8')
        if offset > 127: offset -= 256

        sp_val = self.SP
        result = (sp_val + offset) & 0xFFFF
        self.F = 0 

        if (sp_val & 0x0F) + (offset & 0x0F) > 0x0F: self.F |= FLAG_H
        if (sp_val & 0xFF) + (offset & 0xFF) > 0xFF: self.F |= FLAG_C

        self.H = (result >> 8) & 0x0F
        self.L = result & 0xFF
        return 
    