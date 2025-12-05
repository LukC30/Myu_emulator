import pygame
import sys
from mmu import MMU
from cpu import CPU
from ppu import PPU
# from utils import _print # Logs desligados

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
CYCLES_PER_FRAME = 70224 

ROM_PATH = 'roms/Tetris.gb'

def main(): 
    pygame.init()
    
    memory_unit = MMU()
    memory_unit.load_rom(ROM_PATH)

    # Janela 2x
    screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
    pygame.display.set_caption("Emulador Myu - Tetris")
    
    cpu = CPU(memory_unit)
    ppu = PPU(memory_unit, screen)

    clock = pygame.time.Clock()
    running = True
    
    # Variável do Timer
    div_counter = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
        cycles_this_frame = 0
        while cycles_this_frame < CYCLES_PER_FRAME:
            # 1. CPU
            cycles = cpu.step()
            cycles_this_frame += cycles

            # 2. PPU
            ppu.step(cycles)
            
            # 3. --- LÓGICA DO TIMER (O que falta no teu código) ---
            div_counter += cycles
            if div_counter >= 256:
                div_counter -= 256
                # Incrementa o registro DIV (0xFF04)
                current_div = memory_unit.read_byte(0xFF04)
                memory_unit.memory[0xFF04] = (current_div + 1) & 0xFF
            # -----------------------------------------------------

            if cycles == 0:
                cycles = 4
                cycles_this_frame += 4
                ppu.step(4)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()