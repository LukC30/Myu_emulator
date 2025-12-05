from mmu import MMU
from utils import _print
import pygame

# Cores base do Game Boy (Off, 33%, 66%, 100%)
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
        self.counter = 0
        _print("PPU (Unidade de processamento de video) inicializada")

    def step(self, cycles):
        self.counter += cycles

        # O Game Boy desenha uma linha (scanline) a cada 456 ciclos
        if self.counter >= 456:
            self.counter -= 456
            
            ly = self.mmu.read_byte(0xFF44) # Registrador LY (Linha atual)

            # Se chegamos na linha 144, entramos em V-Blank
            if ly == 144:
                self.render_screen() # Desenha o frame completo
                
                # Solicita Interrupção de V-Blank (Bit 0 do registro IF)
                if_reg = self.mmu.read_byte(0xFF0F)
                self.mmu.write_byte(0xFF0F, if_reg | 0x01)

            # Incrementa LY. Se passar de 153, volta para 0
            ly = (ly + 1) % 154
            self.mmu.write_byte(0xFF44, ly)

    def get_bg_palette(self):
        """Lê o registrador BGP (0xFF47) e retorna as cores mapeadas."""
        bgp = self.mmu.read_byte(0xFF47)
        palette = []
        
        # O BGP define qual cor da lista COLORS corresponde aos IDs 0, 1, 2, 3
        for i in range(4):
            # Extrai 2 bits para cada cor (Bits 0-1, 2-3, etc.)
            color_id = (bgp >> (i * 2)) & 0x03
            palette.append(COLORS[color_id])
            
        return palette

    def render_screen(self):
        lcdc = self.mmu.read_byte(0xFF40)
        
        # Se o LCD estiver desligado, não fazemos nada
        if not (lcdc & 0x80):
            return

        # --- Configurações (Iguais ao anterior) ---
        tile_map_base = 0x9C00 if (lcdc >> 3) & 1 else 0x9800
        tile_data_unsigned = (lcdc >> 4) & 1
        tile_data_base = 0x8000 
        
        scy = self.mmu.read_byte(0xFF42)
        scx = self.mmu.read_byte(0xFF43)
        palette = self.get_bg_palette()

        # Cria um array de pixels para acesso direto (Muito mais rápido que draw.rect)
        # O Pygame trava a superfície para escrita rápida
        pixel_array = pygame.PixelArray(self.screen)
        
        # Escala 2x (hardcoded para simplificar, ideal seria dinâmico)
        scale = 2

        for y in range(144): # Linhas da tela
            
            # Cálculo da posição Y no mapa com Scroll
            map_y = (y + scy) & 0xFF
            row_in_tile = map_y % 8
            tile_y = map_y // 8
            
            for x in range(160): # Colunas da tela
                
                # Cálculo da posição X no mapa com Scroll
                map_x = (x + scx) & 0xFF
                col_in_tile = map_x % 8
                tile_x = map_x // 8
                
                # Busca o ID do Tile
                tile_index = self.mmu.read_byte(tile_map_base + (tile_y * 32) + tile_x)

                # Busca o endereço dos dados
                if tile_data_unsigned:
                    tile_addr = tile_data_base + (tile_index * 16)
                else:
                    if tile_index > 127: tile_index -= 256
                    tile_addr = 0x9000 + (tile_index * 16)

                # Decodificação da cor (2 bits por pixel)
                byte1 = self.mmu.read_byte(tile_addr + (row_in_tile * 2))
                byte2 = self.mmu.read_byte(tile_addr + (row_in_tile * 2) + 1)
                
                bit_index = 7 - col_in_tile
                low = (byte1 >> bit_index) & 1
                high = (byte2 >> bit_index) & 1
                color = palette[(high << 1) | low]

                # --- DESENHO OTIMIZADO ---
                # Preenchemos os 4 pixels (2x2) correspondentes à escala
                # Mapeamos a cor RGB para inteiro que o PixelArray entende
                color_int = self.screen.map_rgb(color)
                
                base_x = x * scale
                base_y = y * scale
                
                # Desenha o quadrado 2x2 manualmente no array
                pixel_array[base_x, base_y] = color_int
                pixel_array[base_x + 1, base_y] = color_int
                pixel_array[base_x, base_y + 1] = color_int
                pixel_array[base_x + 1, base_y + 1] = color_int

        # Destrava a superfície para o Pygame poder desenhar na tela
        pixel_array.close()