from mmu import MMU
from utils import _print
from typing import Tuple

FLAG_Z = 0b10000000 # Bit 7 (Zero Flag)
FLAG_N = 0b01000000 # Bit 6 (Subtract Flag)
FLAG_H = 0b00100000 # Bit 5 (Half-Carry Flag)
FLAG_C = 0b00010000 # Bit 4 (Carry Flag)

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
        
        # começo a pegar o opcode (codigo operacional) a partir do entry point da nossa cpu
        current_pc = self.PC
        opcode = self.mmu.read_byte(self.PC)

        self.PC += 1
        # olha que legal, da pra formatar os numeros em hexadecimal
        # #04x = Hex, preenchido com 0, 2 digitos (0x00)
        # #06x = Hex, preenchido com 0, 4 digitos (0x0000)
        match opcode:
            # Instrução 0x00: NOP
            case 0x00:
                # aqui ele nao faz basicamente nada, ocupa 1 byte e leva 4 ciclos de clock
                pass
            

            #Instrução 0xF3: Interruptor mestre desabilitado
            case 0xF3:
                self.ime = False
                _print(f"0xF3 (DI): Interrupção desabilitada")
            

            #Instrução 0x06: LD B, com d8
            case 0x06:
                # Carrega o operando de 8bits (d8) no registro B
                # Ocupa 2 bytes. Logica quase identicfa ao 0x03
                
                #Ler o operador e carregar no ponteiro B
                value = self.mmu.read_byte(self.PC)
                self.PC += 1

                #Carregando no ponteiro B
                self.B = value

                _print(f"0x06 (LD B, d8): Carregado {value:#04x} para B.")      

            #Instrução 0x3E: Mesma logica do cara de cima
            case 0x3E:
                value = self.mmu.read_byte(self.PC)
                self.PC +=1

                self.A = value
                _print(f"0x3E (LD A, d8): Carregado {value:#04x} para A")
                    

            # Instrução 0x0E: LD C, d8 (lê-se load no registrador c um dado de 8bits)
            case 0x0E:
                #Instrução de 2bytes contendo apenas o 0x0E e o low_byte
                value = self.mmu.read_byte(self.PC)
                self.PC+=1
                self.C = value

                _print(f"0x0E (LD C, d8): Carregado {value:#04x} para registrador C.")

            
            #Instrução 0x20: JR NZ, r8: jump relative if not zero (so vai pular se a flag 0 estiver desligada)
            case 0x20:
                offset = self.mmu.read_byte(self.PC)
                self.PC += 1

                #Aqui fazemos a conversão de 8-bit unsigned (ou seja, positivo e negativo)
                #Para 8-bit signed, ou seja, se for maior que 127, vamos tirar 256 (de forma a resetar a contagem)
                if offset > 127:
                    offset -= 256
                
                if(self.F & FLAG_Z) == 0:
                    target = self.PC + offset
                    _print(f"0x20 (JR NZ, r8): condição verdadeira (Z=0). Pulando {offset} para {target:#06x}")
                    self.PC = target
                
                else:
                    #A condição foi falsa (Z=1). pulamos
                    _print(f"0x20 (JR NZ, r8): condição falsa (Z=1). Continuando...")


            # Instrução 0x21: LD HL, d16 (lê-se load no registrador HL (ou H + L já que são apartados e quando juntos formam um register de 16bits) um dado de 16bit)
            case 0x21: 
                #ocupa 3 bytes por conta do 0x21, low e high_byte
                low_byte = self.mmu.read_byte(self.PC)
                self.PC+=1

                high_byte = self.mmu.read_byte(self.PC)
                self.PC+=1
                
                #Nesse caso o H do self.h foi de high e o l do self.l foi de low huahuahuahu
                self.H = high_byte
                self.L = low_byte

                address = (high_byte << 8) | low_byte
                _print(f"0x21 (LD HL, d16): Carregado {address:#06x} para HL.")

            
            #instrução 0x2A: LDI A, (HL+)
            case 0x2A:

                address = (self.H << 8) | self.L

                value = self.mmu.read_byte(address)
                self.A = value

                address += 1
                address &= 0xFFFF

                self.H = (address >> 8) & 0xFF
                self.L = address & 0xFF
                _print(f"0x2A (LDI A, (HL+)): Carregou {value:#02x} de HL, incrementou HL para {address:#06x}")

            #instrução 0x2f: CPL A
            #Vai inverter to dos os bits do acumulador (A = ~A)
            case 0x2F:
                self.A = (~self.A) & 0xFF

                self.F |= FLAG_N
                self.F |= FLAG_H

                _print(f"0x2F (CPL): Inverteu bits de A para {self.A:#02x}")                
            
            
            #Instrução 0x78, LD A, B
            #Sim, é literalmente só isso
            case 0x78:
                self.A = self.B
                _print(f"0x78 (LD A, B): Copiou B({self.B:#02x}) para A")

            #Instrução 0x79 LD A, C
            case 0x79: 
                self.A = self.C
                _print(f"0x79 (LD A, C): Copiou C({self.C:#02x}) para A")
            
            # Instrução 0xA1: AND C
            # Realiza um E lógico entre A e C.
            # Flags: Z (se zero), N=0, H=1, C=0.
            case 0xA1:
                self.A &= self.C

                if self.A == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
    
                self.F &= ~FLAG_N  
                self.F |= FLAG_H   
                self.F &= ~FLAG_C  

                _print(f"0xA1 (AND C): A({self.A:#02x}) AND C({self.C:#02x})")


            #Instrução 0xA9: XOR C
            case 0xA9:
                self.A = self.A ^ self.C

                if self.A == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                self.F = self.F & (~(FLAG_N | FLAG_H | FLAG_C))
                _print(f"0xA9 (XOR C): Registrador zerado, flag atualizada")


            # Instrução 0xAF: XOR A
            case 0xAF:
                #XOR A com ele mesmo
                self.A = 0x00

                self.F = self.F | FLAG_Z

                self.F = self.F & (~(FLAG_N | FLAG_H | FLAG_C))
                # tem a forma mais facil mas ninguem liga
                # self.F = self.F & (~FLAG_N) # Desliga N
                # self.F = self.F & (~FLAG_H) # Desliga H
                # self.F = self.F & (~FLAG_C) # Desliga C
                _print(f"0xAF (XOR A): Registrador zerado, flag atualizada")

            #Instrução 0xB0: OR B
            case 0xB0:
                self.A = self.A | self.B
                if self.A == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                
                self.F &= ~(FLAG_N | FLAG_H | FLAG_C)
                _print(f"0xB0 (OR B): A({self.A:#02x}) | B({self.B:#02x}) -> A")
            #Mesma coisa do cara debaixo

            #Instrução 0xB1: OR C: vai ser realizado um ou logico entre A e C e verifica se B (que está sendo apontado por A) e c sao 0
            case 0xB1:
                self.A = self.A | self.C

                if self.A == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                
                self.F &= ~(FLAG_N | FLAG_H | FLAG_C)
                _print(f"0xB1 (OR C): Resultado A={self.A:#02x}")

            
            # Instrução 0xC3: JP a16
            case 0xC3:
                #JP a16: jump to adress 16bits (pula para um endereço de 16bit plmds)
                #ocupa 3 bytes (0xC3, low_byte, high_byte)

                low_byte = self.mmu.read_byte(self.PC)
                self.PC+=1

                high_byte = self.mmu.read_byte(self.PC)
                self.PC+=1

                address = (high_byte << 8) | low_byte

                self.PC = address

                _print(f"0xC3 is jump to: {address:#06x}")
            
            #Instrução 0xC9 RET
            #pega o endereço salvo na stack e joga no program counter(PC)
            case 0xC9:
                low_byte = self.mmu.read_byte(self.SP)
                self.SP += 1
                
                high_byte = self.mmu.read_byte(self.SP)
                self.SP += 1

                return_address = (high_byte << 8) | low_byte
                _print(f"0xC9 (RET): Retornando para {return_address:#06x}")

                self.PC = return_address
            
            #Instrução 0xCB: prefixo para operações de bit wtffffffffff
            case 0xCB:
                cb_opcode = self.mmu.read_byte(self.PC)
                self.PC +=1
                
                match cb_opcode:

                    case 0x37:
                        upper_nibble = (self.A & 0xF0)>>4
                        lower_nibble = (self.A & 0x0F)<<4

                        self.A = lower_nibble | upper_nibble

                        if self.A == 0:
                            self.F |= FLAG_Z
                        else: 
                            self.F &= ~FLAG_Z

                        self.F &= ~(FLAG_N | FLAG_H | FLAG_C)

                        _print(f"0xCB 0x37 (SWAP A): Inverteu nibbles de A para {self.A:#02x}")

                    case _:
                        _print(f"PANIC ERROR (CB): opcode estendido desconhecido {cb_opcode:#04x} em: {self.PC-2:#06x}")
                        exit()

            #Instrução 0xCD Call a16
            #vai chamar uma funcao em um endereço de 16bit
            case 0xCD:
                low_byte = self.mmu.read_byte(self.PC)
                self.PC += 1
                high_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                target_address = (high_byte << 8) | low_byte

                self.SP -= 1
                self.mmu.write_byte(self.SP, (self.PC >> 8) & 0xFF)

                self.SP -= 1
                self.mmu.write_byte(self.SP, self.PC & 0xFF)
                
                _print(f"0xCD (CALL a16): call function in {target_address:#06x}. the return is saved in stack: {self.PC:#06x}")
                self.PC = target_address

            #Instrução 0x32: LD (HL-), A
            case 0x32:
                
                #Aqui recuperamos o endereço armazenado no HL juntando os dois
                address = (self.H << 8) | self.L
                
                #Escrevemos o valor de A na memoria, no endereço que acabamos de recuperar em HL
                self.mmu.write_byte(address, self.A)
                
                # decrementamos HL e garantimos que nao fica vazio
                address -= 1
                address &= 0xFFFF
                
                #Atualizamos h e l com o novo valor
                self.H = (address >> 8) & 0xFF
                self.L = address & 0xFF

                _print(f"0x32 (LD (HL-), A): Write A({self.A:02x}) in {(address+1):#06x}, HL dec for {address:#06x}")
            
            #Instrução 0x31: LD SP, d16
            case 0x31:

                low_byte = self.mmu.read_byte(self.PC)
                self.PC +=1

                high_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                self.SP = (high_byte << 8) | low_byte

                _print(f"0x31 (LD SP, d16): Stack Pointer defined for {self.SP:#06x}")
            
            #instrução 0x36: LD (HL), d8
            case 0x36:
                
                value = self.mmu.read_byte(self.PC)
                self.PC += 1

                address = (self.H << 8) | self.L

                self.mmu.write_byte(address, value)
                _print(f"0x36 (LD (HL), d8): Write {value:#02x} in address HL({address:#06x})")

            #Instrução 0x47: LD B, A
            case 0x47:
                self.B = self.A
                _print(f"0x47 (LD B, A): Copiou A({self.A:#02x}) para B")
            
            #instrução 0x4F: LD C, A
            case 0x4F: 
                self.C = self.A
                _print(f"0x4F (LD C, A): Copiou A({self.A:#02x}) para C")

            #Instrução 0x05: (DEC B) B-1
            case 0x05:
                #1 Ajustar a flag H (half carry) para calcular

                #eu nao entendi o 0x05
                if(self.B & 0x0F) == 0:
                    self.F |= FLAG_H
                else:
                    self.F &= ~FLAG_H
                
                self.B = (self.B - 1) & 0xFF
                
                if self.B == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                
                self.F |= FLAG_N
                _print(f"0x05 (DEC B): B decrementado para {self.B:#04x}")

            case 0x01:
                low_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                high_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                self.B = high_byte
                self.C = low_byte

                value = (self.B << 8) | self.C
                _print(f"0x01 (LD BC, d16): Loaded {value:#06x} in BC (b and c)")

            #instrucao 0x0B: decrementando B e C = f familia
            case 0x0B:
                value = (self.B << 8) | self.C
                value = (value - 1) & 0xFFFF

                self.B = (value >> 8) & 0xFF
                self.C = value & 0xFF

                _print(f"0x0B (DEC BC): BC decrementado para {value:#06x}")

            #instrução 0x0C: incrementando C em 1
            case 0x0C:
                if(self.C & 0x0F) == 0x0F:
                    self.F |= FLAG_H
                else:
                    self.F &= ~FLAG_H

                self.C = (self.C + 1) & 0xFF

                if self.C == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                
                self.F &= ~FLAG_N

                _print(f"0x0C (INC C): C incrementado para {self.C:#04x}")                

            #vou tentar organizar o codigo fds
            case 0x0D:
                if(self.C & 0x0F) == 0:
                    self.F |= FLAG_H
                else:
                    self.F &= ~FLAG_H
                
                self.C = (self.C - 1) & 0xFF
                if self.C == 0:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z
                self.F |= FLAG_N
                _print(f"0x0D (DEC C): C decrementado para {self.C:#04x}")


            #Instrução 0xE0 LDH (a8): vai carregar o valor de A na memoria "Alta"
            case 0xE0:
                #Aqui a gente vai começar a ter contato com o hardware. vamos pegar o valor que é descrito aqui e somar ao endereço especial da memoria pra hard
                offset = self.mmu.read_byte(self.PC)
                self.PC +=1
                
                address = 0xFF00 + offset

                self.mmu.write_byte(address, self.A)
                _print(f"0xE0 (LDH (a8), A): Escreve A({self.A:#02x} em {address:#06x})")

            #Instrução 0xE2
            case 0xE2:
                address = 0xFF00 + self.C
                self.mmu.write_byte(address, self.A)
                _print(f"0xE2 (LD (C), A): Escreveu A({self.A:#02x}) na porta de I/O 0xFF00+C ({address:#06x})")

            #Instrução 0xE6: AND d8 (Realiza E logico entre A e o valor imediato)
            case 0xE6:
                value = self.mmu.read_byte(self.PC)
                self.PC += 1

                self.A &= value

                if self.A == 0:
                    self.F |= FLAG_Z
                else: 
                    self.F &= ~FLAG_Z

                self.F &= ~FLAG_N
                self.F |= FLAG_H
                self.F &= ~FLAG_C
                _print(f"0xE6 (AND d8): A({self.A:#02x}) AND {value:#02x}")

            case 0xEA:

                low_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                high_byte = self.mmu.read_byte(self.PC)
                self.PC += 1

                address = (high_byte << 8) | low_byte
                
                self.mmu.write_byte(address, self.A)
                _print(f"0xEA (LD (a16), A): Armazenou A({self.A:#02x}) no endereço {address:#06x}")

            #Instrução 0xF0 LDH A, (a8)
            case 0xF0:
                
                offset = self.mmu.read_byte(self.PC)
                self.PC += 1
                address = 0xFF00 + offset

                value = self.mmu.read_byte(address)
                self.A = value

                _print(f"0xF0 (LDH A, (a8)): Leu {value:#02x} de {address:#06x} para A")
            
            #Instrução 0xFB: EI (habilitar interrupções)
            case 0xFB:
                self.ime = True
                _print(f"0xFB (EI): Interrupções Habilitadas (IME = True)")
            
            #Instrução 0xFE:
            case 0xFE: 
                value = self.mmu.read_byte(self.PC)
                self.PC += 1

                # CORREÇÃO 1: A lógica é igualdade (ou subtração resultando em 0)
                if self.A == value:
                    self.F |= FLAG_Z
                else:
                    self.F &= ~FLAG_Z

                # CORREÇÃO 2: Flag N (Subtract) deve ser SEMPRE ligada em CP
                self.F |= FLAG_N

                # Half Carry (Se o nibble baixo de A for menor, houve empréstimo)
                if (self.A & 0x0F) < (value & 0x0F):
                    self.F |= FLAG_H
                else:
                    self.F &= ~FLAG_H
                
                # Carry (Se A for menor que o valor, houve empréstimo/underflow)
                if self.A < value:
                    self.F |= FLAG_C
                else: 
                    self.F &= ~FLAG_C

                _print(f"0xFE (CP d8): Comparou A({self.A:#02x}) com {value:#02x}")

            

            case _:
                # Aqui so se o opcode for desconhecido
                _print(f"PANIC ERROR: opcode desconhecido kkkkkkkk no {opcode:#04x} em: {self.PC-1:#06x}")
                exit() #so tirar esse cara aqui depois
                pass
