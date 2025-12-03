from mmu import MMU
from utils import _print

class PPU():

    def __init__(self, mmu: MMU):
        self.mmu = mmu
        _print("PPU (Unidade de processamento de video) inicializadaS")
        

    def step(self):
        ly = self.mmu.read_byte(0xFF44)

        ly = (ly + 1) % 154

        self.mmu.write_byte(0xFF44, ly)
        pass