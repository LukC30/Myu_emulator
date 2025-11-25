from utils import _print

class MMU():
    def __init__(self):

        self.memory = bytearray(65536)
        _print("MMU inicializada com 64kb")

    def read_byte(self, address):
        return self.memory[address]
    
    def write_byte(self, address, value):
        
        if address < 0x8000:
            _print(f"Aviso: Tentativa de escrita na ROM no endereço {address:#06x}")
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