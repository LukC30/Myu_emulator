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
        """Renderiza a tela inteira levando em conta Scroll e Paleta."""
        lcdc = self.mmu.read_byte(0xFF40)

        # Se o bit 7 do LCDC estiver desligado, a tela está desligada
        if not (lcdc & 0x80):
            return

        # 1. Configurações de Mapa e Dados
        # Bit 3: Mapa de Tiles do Background (0=9800-9BFF, 1=9C00-9FFF)
        tile_map_base = 0x9C00 if (lcdc >> 3) & 1 else 0x9800

        # Bit 4: Dados dos Tiles (0=8800-97FF, 1=8000-8FFF)
        tile_data_unsigned = (lcdc >> 4) & 1
        tile_data_base = 0x8000 

        # 2. Leitura de Scroll
        scy = self.mmu.read_byte(0xFF42) # Scroll Y
        scx = self.mmu.read_byte(0xFF43) # Scroll X
        
        # 3. Obter Paleta atual
        palette = self.get_bg_palette()

        scale = 2 # Escala para renderização no Pygame

        # --- Loop de Renderização (Pixel a Pixel / Linha a Linha) ---
        # Percorre as 144 linhas da tela do Game Boy
        for y in range(144):
            
            # Calcula a posição vertical real no mapa de 256x256 (com wrap-around)
            map_y = (y + scy) & 0xFF
            
            # Em qual linha dentro do tile (0-7) estamos?
            row_in_tile = map_y % 8
            
            # Qual a coordenada Y do tile no mapa (0-31)?
            tile_y = map_y // 8

            for x in range(160):
                # Calcula a posição horizontal real no mapa
                map_x = (x + scx) & 0xFF
                
                col_in_tile = map_x % 8
                tile_x = map_x // 8

                # Calcula o endereço do ID do tile no mapa
                # Mapa tem 32 tiles de largura
                tile_index_address = tile_map_base + (tile_y * 32) + tile_x
                tile_index = self.mmu.read_byte(tile_index_address)

                # Calcula o endereço dos dados do tile (16 bytes por tile)
                if tile_data_unsigned:
                    # Modo 8000 (0 a 255)
                    tile_addr = tile_data_base + (tile_index * 16)
                else:
                    # Modo 8800 (-128 a 127)
                    if tile_index > 127:
                        tile_index -= 256
                    tile_addr = 0x9000 + (tile_index * 16)

                # Lê os 2 bytes que definem a linha de pixels atual
                # Cada linha de 8 pixels usa 2 bytes
                byte1 = self.mmu.read_byte(tile_addr + (row_in_tile * 2))
                byte2 = self.mmu.read_byte(tile_addr + (row_in_tile * 2) + 1)

                # Decodifica a cor do pixel
                # Bit 7 é o pixel mais à esquerda (0), Bit 0 é o pixel 7
                bit_index = 7 - col_in_tile
                low = (byte1 >> bit_index) & 1
                high = (byte2 >> bit_index) & 1

                color_index = (high << 1) | low
                
                # Mapeia para a cor real usando a paleta
                color = palette[color_index]

                # Desenha o pixel na tela do Pygame
                # Usamos rect para garantir que o pixel preencha o espaço da escala (evita buracos)
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        x * scale, 
                        y * scale, 
                        scale, 
                        scale
                    )
                )