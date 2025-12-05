import pygame
import sys
from mmu import MMU
from cpu import CPU
from ppu import PPU
from utils import _print

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144

ROM_PATH = 'roms/Tetris.gb'

def main(): 
    pygame.init()
    
    memory_unit = MMU()
    memory_unit.load_rom(ROM_PATH)

    screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
    pygame.display.set_caption("Emulador myu")
    cpu = CPU(memory_unit)
    ppu = PPU(memory_unit, screen)

    running = True
    while running:

        for event in pygame.event.get():
            # aqui so para se o bagui for false, ai ele detona tudo
            if event.type == pygame.QUIT:
                running = False
            
        for _ in range(1000):
            cycles_spent = cpu.step()

            ppu.step(cycles_spent)
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_RETURN:
            #         _print("(Enter pressionado)")
                    # cpu.step()

        
        pygame.display.flip()

    pygame.quit()
    _print("Encerrado")
    sys.exit()

if __name__ == '__main__':
    main()