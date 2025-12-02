from mmu import MMU
from utils import _print

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
        self.A = 0x00
        self.F = 0x00
        self.B = 0x00
        self.C = 0x00
        self.D = 0x00
        self.E = 0x00
        self.H = 0x00
        self.L = 0x00

        # Ponteiros de 16bit (Stack pointer e Program counter)
        self.SP = 0x0000
        self.PC = 0x0100 #ele ta iniciando a partir do bit256 (em decimal)
        
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
            
            #Instrução 0x06: LB B, com d8
            case 0x06:
                # Carrega o operando de 8bits (d8) no registro B
                # Ocupa 2 bytes. Logica quase identicfa ao 0x03
                
                #Ler o operador e carregar no ponteiro B
                value = self.mmu.read_byte(self.PC)
                self.PC += 1

                #Carregando no ponteiro B
                self.B = value

                _print(f"0x06 (LD B, d8): Carregado {value:#04x} para B.")          


            # Instrução 0x0E: LD C, d8 (lê-se load no registrador c um dado de 8bits)
            case 0x0E:
                #Instrução de 2bytes contendo apenas o 0x0E e o low_byte
                value = self.mmu.read_byte(self.PC)
                self.PC+=1
                self.C = value

                _print(f"0x0E (LD C, d8): Carregado {value:#04x} para registrador C.")


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

            # Instrução 0xC3: JP 

            #Instrução 0x32: LD (HL-), A
            case 0x32:

                address = (self.H << 8) | self.L
                
                self.mmu.write_byte(address, self.A)
                address -= 1
                address &= 0xFFFF
                
                self.H = (address >> 8) & 0xFF
                self.L = address & 0xFF

                _print(f"0x32 (LD (HL-), A): Escreveu A({self.A:02x}) em {(address+1):#06x}, HL dec para {address:#06x}")

            case _:
                # Aqui so se o opcode for desconhecido
                _print(f"PANIC ERROR: opcode desconhecido kkkkkkkk no {opcode:#04x} em: {self.PC-1:#06x}")
                pass
