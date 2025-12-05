from mmu import MMU
from utils import _print
from instruction_set import instructions

FLAG_Z = 0x80 # Bit 7 (Zero Flag)
FLAG_N = 0x40 # Bit 6 (Subtract Flag)
FLAG_H = 0x20 # Bit 5 (Half-Carry Flag)
FLAG_C = 0x10 # Bit 4 (Carry Flag)

class CPU:
    def __init__(self, mmu: MMU):
        _print("CPU inicializada")
        # aqui eu guardo a referencia ao objeto da MMU
        self.mmu = mmu

        # Ponteiros de 8bit (Registradores)
        self.A = 0x01
        self.F = 0xB0
        self.B = 0x00
        self.C = 0x13
        self.D = 0x00
        self.E = 0xD8
        self.H = 0x01
        self.L = 0x4D

        # Ponteiros de 16bit (Stack pointer e Program counter)
        self.SP = 0xFFFE
        self.PC = 0x0100 #ele ta iniciando a partir do bit256 (em decimal)
        
        #Interrupt Master Enable (IME)
        self.ime = False

        _print(f"Ponto de entrada (PC(Program Counter)) definido para {self.PC} ou 0x0100")

    def step(self):
        opcode = self.mmu.read_byte(self.PC)

        if opcode not in instructions:
            _print(f"PANIC: Opcode desconhecido {opcode:#04x} em {self.PC:#06x}")
            exit()

        instr = instructions[opcode]
        self.PC += 1

        parts = instr.name.split('_')
        operation = parts[0]

        method = getattr(self, f'op_{operation}', None)

        if method:
            method(instr, parts)
        else:
            _print(f"Aviso: Handler não implementado para {instr.name}")
            exit()

    
    def get_operand_value(self, operand_str):
        match operand_str:
            # --- Registradores de 8 bits ---
            case 'A': return self.A
            case 'B': return self.B
            case 'C': return self.C
            case 'D': return self.D
            case 'E': return self.E
            case 'H': return self.H
            case 'L': return self.L

            # --- Registradores de 16 bits ---
            case 'AF': return (self.A << 8) | self.F
            case 'BC': return (self.B << 8) | self.C
            case 'DE': return (self.D << 8) | self.E
            case 'HL': return (self.H << 8) | self.L
            case 'SP': return self.SP

            # --- Acesso à Memória (Com efeitos colaterais!) ---
            case 'd8' | 'a8' | 'r8':
                val = self.mmu.read_byte(self.PC)
                self.PC += 1
                return val
            
            case 'd16' | 'a16':
                low = self.mmu.read_byte(self.PC)
                self.PC += 1
                high = self.mmu.read_byte(self.PC)
                self.PC += 1
                return (high << 8) | low

            case '(HL)':
                addr = (self.H << 8) | self.L
                return self.mmu.read_byte(addr)

            case '(HL+)':
                val = self.mmu.read_byte((self.H << 8) | self.L)
                self.increment_hl()
                return val
            
            case '(HL-)':
                val = self.mmu.read_byte((self.H << 8) | self.L)
                self.decrement_hl()
                return val

            case '(C)':
                 return self.mmu.read_byte(0xFF00 + self.C)
        
            case _:
                _print(f"ERRO: Operando desconhecido {operand_str}")
                return 0

    def set_operand_value(self, dest, value):
        match dest:    
            #para registradores 8 bits
            case 'A':  self.A = value
            case 'B':  self.B = value
            case 'C':  self.C = value
            case 'D':  self.D = value
            case 'E':  self.E = value
            case 'H':  self.H = value
            case 'L':  self.L = value

            #para registradores 16 bits (juncao de 2 de 8bits, pq essa eh a safadeza)
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
                self.SP = value

            #memoria indireta mds
            case '(HL)':
                addr = (self.H << 8) | self.L
                self.mmu.write_byte(addr, value)

            case '(HL+)':
                self.mmu.write_byte((self.H << 8) | self.L, value)
                self.increment_hl()
                
            case '(HL-)':
                self.mmu.write_byte((self.H << 8) | self.L, value)
                self.decrement_hl()
            
            case '(C)':
                address = 0xFF00 + self.C
                self.mmu.write_byte(address, value)
            
            case '(a16)':
                low = self.mmu.read_byte(self.PC)
                self.PC += 1
                high = self.mmu.read_byte(self.PC)
                self.PC += 1
                addr = (high << 8) | low
                
                # Escreve o valor nesse endereço
                self.mmu.write_byte(addr, value)
    
    # ALU: Soma de 8 bits (Usada por ADD e ADC)
    def alu_add(self, value, carry=False):
        c_val = 1 if (carry and (self.F & FLAG_C)) else 0
        result = self.A + value + c_val
        
        self.F = 0
        if (result & 0xFF) == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) + (value & 0x0F) + c_val > 0x0F: self.F |= FLAG_H
        if result > 0xFF: self.F |= FLAG_C
        
        self.A = result & 0xFF
        _print(f"ALU ADD: Result {self.A:#02x}")
        
    def add_16_bit(self, source):
        # 1. Pega os valores
        hl = (self.H << 8) | self.L
        value = self.get_operand_value(source)

        # 2. Soma
        result = hl + value

        # 3. Flags (Atenção: ADD HL não muda Z!)
        self.F &= ~FLAG_N # N = 0
        
        # Half-Carry (Overflow do bit 11)
        if (hl & 0x0FFF) + (value & 0x0FFF) > 0x0FFF:
            self.F |= FLAG_H
        else:
            self.F &= ~FLAG_H
            
        # Carry (Overflow do bit 15)
        if result > 0xFFFF:
            self.F |= FLAG_C
        else:
            self.F &= ~FLAG_C

        # 4. Salva em HL (mantendo 16 bits)
        result &= 0xFFFF
        self.H = (result >> 8) & 0xFF
        self.L = result & 0xFF


    def op_NOP(self, inst, parts):
        pass

    def op_ADD(self, inst, parts):   
        target = parts[1]
        source = parts[2]

        if target == 'HL':
            self.add_16_bit(source)
            return

        # Lógica 8 bits (ADD A, r)
        val = self.get_operand_value(source)
        self.alu_add(val, carry=False)
    
    def op_ADC(self, inst, parts):
        source = parts[2]
        val = self.get_operand_value(source)
        self.alu_add(val, carry=False)

    def op_LD(self, inst, parts):
        dest_str = parts[1]
        src = parts[2]

        value = self.get_operand_value(src)
        
        self.set_operand_value(dest_str, value)

        _print(f"{inst.name}: Carregou {value:#04x} em {dest_str}")
    def op_INC(self, inst, parts):
        target = parts[1]
        
        # 16 Bits (Não afeta flags)
        if target in ['BC', 'DE', 'HL', 'SP']:
            val = self.get_operand_value(target)
            val = (val + 1) & 0xFFFF
            self.set_operand_value(target, val)
            return

        # 8 Bits (Afeta Z, N, H)
        val = self.get_operand_value(target)
        result = (val + 1) & 0xFF
        self.set_operand_value(target, result)

        self.F &= ~FLAG_N # N=0
        if result == 0: self.F |= FLAG_Z
        else: self.F &= ~FLAG_Z
        
        if (val & 0x0F) + 1 > 0x0F: self.F |= FLAG_H
        else: self.F &= ~FLAG_H

    def op_DEC(self, inst, parts):
        target = parts[1]
        
        # 16 Bits
        if target in ['BC', 'DE', 'HL', 'SP']:
            val = self.get_operand_value(target)
            val = (val - 1) & 0xFFFF
            self.set_operand_value(target, val)
            return

        # 8 Bits
        val = self.get_operand_value(target)
        result = (val - 1) & 0xFF
        self.set_operand_value(target, result)

        self.F |= FLAG_N # N=1
        if result == 0: self.F |= FLAG_Z
        else: self.F &= ~FLAG_Z

        if (val & 0x0F) == 0: self.F |= FLAG_H
        else: self.F &= ~FLAG_H

    def op_AND(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A &= val
        self.update_logic_flags(h=True) # AND seta H=1 por padrão no GB

    def op_OR(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A |= val
        self.update_logic_flags(h=False)

    def op_XOR(self, inst, parts):
        val = self.get_operand_value(parts[1])
        self.A ^= val
        self.update_logic_flags(h=False)

    def op_CP(self, inst, parts):
        # CP é uma subtração que não salva o resultado
        val = self.get_operand_value(parts[1])
        # Reutilizamos a lógica de subtração (que você pode criar ou copiar do op_SUB)
        # Aqui vou fazer direto para simplificar:
        res = self.A - val
        
        self.F = FLAG_N # Seta N
        if res == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) < (val & 0x0F): self.F |= FLAG_H
        if self.A < val: self.F |= FLAG_C

    def update_logic_flags(self, h):
        self.F = 0
        if self.A == 0: self.F |= FLAG_Z
        if h: self.F |= FLAG_H

    def op_PUSH(self, inst, parts):
        # PUSH BC -> empurra BC
        val = self.get_operand_value(parts[1])
        self.SP -= 1
        self.mmu.write_byte(self.SP, (val >> 8) & 0xFF)
        self.SP -= 1
        self.mmu.write_byte(self.SP, val & 0xFF)

    def op_POP(self, inst, parts):
        low = self.mmu.read_byte(self.SP)
        self.SP += 1
        high = self.mmu.read_byte(self.SP)
        self.SP += 1
        val = (high << 8) | low
        
        target = parts[1]
        if target == 'AF':
            # Cuidado: Bits baixos de F são sempre zero
            val &= 0xFFF0
        
        self.set_operand_value(target, val)

    def op_JP(self, inst, parts):
        # JP a16 ou JP NZ, a16
        if len(parts) > 2: # Condicional (JP NZ a16)
            cond = parts[1]
            dest = self.get_operand_value(parts[2]) # Lê o endereço
            if self.check_condition(cond):
                self.PC = dest
        else: # Incondicional (JP a16 ou JP (HL))
            dest = self.get_operand_value(parts[1])
            self.PC = dest

    def op_JR(self, inst, parts):
        # JR r8 ou JR NZ, r8
        offset = 0
        jump = True
        
        if len(parts) > 2: # Condicional
            cond = parts[1]
            # O get_operand_value lê o byte assinado? Não, lê unsigned.
            # Precisamos converter para signed (r8)
            raw_offset = self.get_operand_value(parts[2])
            if not self.check_condition(cond):
                jump = False
        else: # Incondicional
            raw_offset = self.get_operand_value(parts[1])

        # Converte para signed
        if raw_offset > 127: raw_offset -= 256
        
        if jump:
            self.PC += raw_offset

    def op_CALL(self, inst, parts):
        # CALL a16 ou CALL NZ, a16
        dest = 0
        should_call = True
        
        if len(parts) > 2: # Condicional
            dest = self.get_operand_value(parts[2])
            if not self.check_condition(parts[1]):
                should_call = False
        else:
            dest = self.get_operand_value(parts[1])
            
        if should_call:
            # Push PC
            self.SP -= 1
            self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)
            self.SP -= 1
            self.mmu.write_byte(self.SP, self.PC & 0xFF)
            self.PC = dest

    def op_RET(self, inst, parts):
        # RET ou RET NZ
        if len(parts) > 1: # Condicional
            if not self.check_condition(parts[1]):
                return # Não retorna

        # Pop PC
        low = self.mmu.read_byte(self.SP)
        self.SP += 1
        high = self.mmu.read_byte(self.SP)
        self.SP += 1
        self.PC = (high << 8) | low

    def check_condition(self, cond):
        if cond == 'NZ': return not (self.F & FLAG_Z)
        if cond == 'Z': return (self.F & FLAG_Z)
        if cond == 'NC': return not (self.F & FLAG_C)
        if cond == 'C': return (self.F & FLAG_C)
        return False
    
    def op_DI(self, inst, parts): self.ime = False
    def op_EI(self, inst, parts): self.ime = True
    def op_NOP(self, inst, parts): pass
    def op_HALT(self, inst, parts): _print("HALT (Não implementado fully)")
    def op_STOP(self, inst, parts): pass
    
    # Rotações Básicas
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
        # Ex: SUB_A_B -> parts[2] é a origem
        val = self.get_operand_value(parts[2])
        
        result = self.A - val
        
        self.F = FLAG_N # N sempre 1 na subtração
        
        if result == 0: self.F |= FLAG_Z
        if (self.A & 0x0F) < (val & 0x0F): self.F |= FLAG_H # Half Borrow
        if self.A < val: self.F |= FLAG_C # Full Borrow/Carry
        
        self.A = result & 0xFF
    
    def op_RST(self, inst, parts):
        # O nome é RST_38H. O destino está na parte [1] ("38H")
        # Remove o 'H' e converte de Hex para Int
        dest_str = parts[1].replace('H', '')
        dest = int(dest_str, 16)
        
        self.SP -= 1
        self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)
        self.SP -= 1
        self.mmu.write_byte(self.SP, self.PC & 0xFF)
        
        # 2. Pula para o endereço fixo
        self.PC = dest
        _print(f"{inst.name}: Chamando rotina em {self.PC:#06x}")
    
    def op_LDH(self, inst, parts):
        dest = parts[1]
        src = parts[2]

        if dest == '(a8)':
            offset = self.get_operand_value('a8')
            address = 0xFF00 + offset
            
            val = self.get_operand_value(src) # src é 'A'
            
            self.mmu.write_byte(address, val)
            _print(f"{inst.name}: Escreveu A({val:#02x}) na porta 0xFF{offset:02x}")

        elif src == '(a8)':
            offset = self.get_operand_value('a8')
            address = 0xFF00 + offset
            
            val = self.mmu.read_byte(address)
            
            self.set_operand_value(dest, val) 
            _print(f"{inst.name}: Leu {val:#02x} da porta 0xFF{offset:02x}")

    def op_PREFIX(self, inst, parts):
        cb_opcode = self.mmu.read_byte(self.PC)
        self.PC += 1

        reg_id = cb_opcode & 0x07
        bit = (cb_opcode >> 3) & 0x07
        operation = (cb_opcode >> 6) & 0x03
        
        reg_map = {0: 'B', 1: 'C', 2: 'D', 3: 'E', 4: 'H', 5: 'L', 6: '(HL)', 7: 'A'}
        operand_str = reg_map[reg_id]

        if operation == 1: 
            val = self.get_operand_value(operand_str)
            is_set = (val >> bit) & 1
            
            if is_set == 0:
                self.F |= FLAG_Z
            else:
                self.F &= ~FLAG_Z
            
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
            
        # 0. Rotações (RLC, RRC, RL, RR, SLA, SRA, SWAP, SRL)
        elif operation == 0:
            pass

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

    