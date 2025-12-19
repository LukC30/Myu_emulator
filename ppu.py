from mmu import MMU
import pygame

COLORS = [
    (255, 255, 255), (192, 192, 192), (96, 96, 96), (0, 0, 0)
]

class PPU:
    def __init__(self, mmu: MMU, screen):
        self.mmu = mmu
        self.screen = screen
        self.counter = 0
        # Buffer de bytes RGB (Muito rápido)
        self.buffer = bytearray(160 * 144 * 3)
        print("PPU (Buffer Mode) inicializada")

    def step(self, cycles):
        self.counter += cycles
        
        if self.counter >= 456:
            self.counter -= 456
            ly = self.mmu.read_byte(0xFF44)
            
            # Renderiza apenas no final da tela visível (Linha 144)
            if ly == 144:
                self.render_screen()
                # Solicita Interrupção VBlank (Bit 0)
                if_reg = self.mmu.read_byte(0xFF0F)
                self.mmu.write_byte(0xFF0F, if_reg | 0x01)

            ly = (ly + 1) % 154
            self.mmu.write_byte(0xFF44, ly)

    def get_bg_palette(self):
        bgp = self.mmu.read_byte(0xFF47)
        return [COLORS[(bgp >> (i * 2)) & 0x03] for i in range(4)]

    def render_screen(self):
        lcdc = self.mmu.read_byte(0xFF40)
        # Se LCD desligado, não desenha (evita lixo na tela)
        if not (lcdc & 0x80): return

        tile_map_base = 0x9C00 if (lcdc >> 3) & 1 else 0x9800
        tile_data_unsigned = (lcdc >> 4) & 1
        tile_data_base = 0x8000 
        
        scy = self.mmu.read_byte(0xFF42)
        scx = self.mmu.read_byte(0xFF43)
        palette = self.get_bg_palette()
        read_byte = self.mmu.read_byte 
        
        idx = 0
        for y in range(144):
            map_y = (y + scy) & 0xFF
            row_in_tile = map_y % 8
            tile_y = map_y // 8
            row_map_addr_base = tile_map_base + (tile_y * 32)

            for x in range(160):
                map_x = (x + scx) & 0xFF
                col_in_tile = map_x % 8
                tile_x = map_x // 8
                
                tile_index = read_byte(row_map_addr_base + tile_x)

                if tile_data_unsigned:
                    tile_addr = tile_data_base + (tile_index * 16)
                else:
                    if tile_index > 127: tile_index -= 256
                    tile_addr = 0x9000 + (tile_index * 16)

                byte1 = read_byte(tile_addr + (row_in_tile * 2))
                byte2 = read_byte(tile_addr + (row_in_tile * 2) + 1)
                
                bit_index = 7 - col_in_tile
                low = (byte1 >> bit_index) & 1
                high = (byte2 >> bit_index) & 1
                
                r, g, b = palette[(high << 1) | low]
                
                self.buffer[idx] = r
                self.buffer[idx+1] = g
                self.buffer[idx+2] = b
                idx += 3

        # Cria a imagem e escala (Blit corrige o formato)
        image = pygame.image.frombuffer(self.buffer, (160, 144), 'RGB')
        scaled_image = pygame.transform.scale(image, (320, 288))
        self.screen.blit(scaled_image, (0, 0))