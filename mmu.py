from utils import _print

class MMU():
    def __init__(self):

        self.memory = bytearray(65536)
        _print("MMU inicializada com 64kb")
        self.buttons = {
            'a': False,
            'b': False,
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'start': False,
            'select': False,
        }

    def read_byte(self, address):
        if address == 0xFF00:
            joypad_register = self.memory[0xFF00]

            
            result = 0xCF
            
            #vamos verificar o bit 4, para ver se estamos lendo direcionais
            if not (joypad_register & 0x10):
                if self.buttons['right']: result &= ~(1 << 0)
                if self.buttons['left']:  result &= ~(1 << 1)
                if self.buttons['up']:    result &= ~(1 << 2)
                if self.buttons['down']:  result &= ~(1 << 3)
                
            if not (joypad_register & 0x20):
                if self.buttons['a']:      result &= ~(1 << 0)
                if self.buttons['b']:      result &= ~(1 << 1)
                if self.buttons['select']: result &= ~(1 << 2)
                if self.buttons['start']:  result &= ~(1 << 3)
            return result
            
        return self.memory[address]
    
    def write_byte(self, address, value):
        
        # protegendo a ROM
        if address < 0x8000:
            return
        
        #endereço dos sprites
        if address == 0xFF46:
            start_address = value << 8 
            for i in range(160): 
                data = self.read_byte(start_address + i)
                self.memory[0xFE00 + i] = data
            
            self.memory[address] = value & 0xFF
            return 
        
        #aqui será feito uma proteção, de forma que apenas os bits 4 e 5, sejam alteraveis, o restante é
        #apenas read only, no caso, os bits inferiores
        if address == 0xFF:
            self.memory[address] = (value & 0xF0) | (self.memory[address] & 0x0F)
            return

        self.memory[address] = value & 0xFF

    def load_rom(self, rom_path):
        """
        Vai carregar nosso arquivo ROM para o inicio da nossa memória (0x0000 -> endereço)
        """
        _print(f"Tentando carregar a ROM: {rom_path}")
        try:
            with open(rom_path, 'rb') as file:
                # lendo a rom com modo binario
                rom_data = file.read()
                for i in range(len(rom_data)):
                    self.memory[i] = rom_data[i]
                _print(f'ROM carregada com sucesso!!!!! Utilizando ({len(rom_data)}) bytes')

        except FileNotFoundError:
            _print(f"ERROR: Arquivo da rom não encontrado no caminho: {rom_path}")

        except Exception as e:
            _print(f'ERROR: Ocorreu um erro ao carregar a rom: {e}')