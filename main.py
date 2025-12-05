import pygame
import sys
from mmu import MMU
from cpu import CPU
from ppu import PPU
from utils import _print

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
CYCLES_PER_FRAME = 70224 # Game Boy roda a ~4.19MHz / 60fps

ROM_PATH = 'roms/Tetris.gb'

def main(): 
    pygame.init()
    
    memory_unit = MMU()
    memory_unit.load_rom(ROM_PATH)

    # Cria a tela (escala 2x para ver melhor)
    screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
    pygame.display.set_caption("Emulador Myu - Tetris")
    
    cpu = CPU(memory_unit)
    ppu = PPU(memory_unit, screen)

    clock = pygame.time.Clock()
    running = True
    
    while running:
        # 1. Eventos do Pygame (Janela e Inputs futuros)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
        # 2. Executar UM FRAME inteiro do Game Boy
        cycles_this_frame = 0
        while cycles_this_frame < CYCLES_PER_FRAME:
            # Avança a CPU
            cycles = cpu.step()
            cycles_this_frame += cycles

            # Avança a PPU (para ela saber quando desenhar a linha/VBlank)
            ppu.step(cycles)
            
            # Se a CPU parou (STOP), forçamos o tempo a andar para não travar
            if cycles == 0:
                cycles = 4
                cycles_this_frame += 4
                ppu.step(4)

        # 3. Atualiza a tela do PC (apenas 1 vez por frame, a 60fps)
        pygame.display.flip()
        
        # Limita a velocidade do emulador para não rodar rápido demais no seu PC
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()