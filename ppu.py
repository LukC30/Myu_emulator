from mmu import MMU
from utils import _print
import pygame

COLORS = [
    (255, 255, 255), # 00: Branco
    (192, 192, 192), # 01: Cinza Claro
    (96, 96, 96),    # 10: Cinza Escuro
    (0, 0, 0)        # 11: Preto
]

class PPU():

    def __init__(self, mmu: MMU, screen):
        self.mmu = mmu
        self.screen = screen
        _print("PPU (Unidade de processamento de video) inicializadaS")
        

    def step(self):
        ly = self.mmu.read_byte(0xFF44)

        if ly == 144:
            self.render_tiles()

        ly = (ly + 1) % 154
        self.mmu.write_byte(0xFF44, ly)
        pass


    def render_tiles(self):
        print("DEBUG: Tentando desenhar tiles na tela!") 
        xd = 0
        yd = 0
        scale = 2

        for address in range(0x8000, 0x9800, 16):

            for y in range(8):

                byte1 = self.mmu.read_byte(address + (y*2))
                byte2 = self.mmu.read_byte(address + (y*2) + 1)

                for x in range(8):
                    bit_index = 7 - x
                    low = (byte1 >> bit_index) & 1
                    high = (byte2 >> bit_index) & 1

                    color_index = (high << 1) | low
                    color = COLORS[color_index]
                    pygame.draw.rect(
                        self.screen,
                        color,
                        (xd + x * scale, yd + y * scale, scale, scale)
                    )
            xd += 8 * scale
            if xd >= 160 * scale:
                xd = 0
                yd += 8 * scale