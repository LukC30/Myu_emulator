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
            self.render_screen()

        ly = (ly + 1) % 154
        self.mmu.write_byte(0xFF44, ly)


    def render_screen(self):
        tile_map_base = 0x9800
        tile_data_base = 0x8000

        # CORREÇÃO 1: O Game Boy tem 18 linhas de tiles (144px / 8 = 18)
        for y in range(18):
            for x in range(20):
                tile_index_address = tile_map_base + (y*32) + x
                tile_index = self.mmu.read_byte(tile_index_address)
                
                # Para Tetris (e modo 8000), isso está correto
                tile_addr = tile_data_base + (tile_index * 16)

                self.render_tiles(x*8, y*8, tile_addr)

    def render_tiles(self, pos_x, pos_y, tile_addr):
        scale = 2

        # CORREÇÃO 2: Use 'row' para as linhas verticais
        for row in range(8):
            
            # Lê os 2 bytes que formam a linha de pixels
            byte1 = self.mmu.read_byte(tile_addr + (row*2))
            byte2 = self.mmu.read_byte(tile_addr + (row*2) + 1)

            # Loop interno para as colunas (pixels horizontais)
            for col in range(8):
                bit_index = 7 - col
                low = (byte1 >> bit_index) & 1
                high = (byte2 >> bit_index) & 1

                color_index = (high << 1) | low
                color = COLORS[color_index]
                
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        (pos_x + col) * scale,  # X varia com a coluna
                        (pos_y + row) * scale,  # Y varia com a linha (CORREÇÃO 3)
                        scale, 
                        scale
                    )
                )