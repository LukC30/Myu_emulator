import pygame
import sys
from mmu import MMU
from cpu import CPU
from ppu import PPU

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
CYCLES_PER_FRAME = 70224 

ROM_PATH = 'roms/Tetris.gb'

key_map = {
    pygame.K_RETURN: 'start',
    pygame.K_RSHIFT: 'select',
    pygame.K_z: 'a',
    pygame.K_x: 'b',
    pygame.K_UP: 'up',
    pygame.K_DOWN: 'down',
    pygame.K_LEFT: 'left',
    pygame.K_RIGHT: 'right'
}

def main(): 
    pygame.init()
    
    memory_unit = MMU()
    memory_unit.load_rom(ROM_PATH)

    # Configuração da Janela (2x escala)
    screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
    pygame.display.set_caption("Emulador Myu - Tetris")
    
    cpu = CPU(memory_unit)
    ppu = PPU(memory_unit, screen)

    clock = pygame.time.Clock()
    running = True

    div_counter = 0
    
    btn_cooldowns = {k: 0 for k in key_map.values()}

    while running:

        for btn in btn_cooldowns:
            if btn_cooldowns[btn] > 0:
                btn_cooldowns[btn] -=1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key in key_map:
                    btn = key_map[event.key]
                    if btn_cooldowns[btn] == 0:
                        memory_unit.press_button(btn) 
                        btn_cooldowns[btn] = 15

            if event.type == pygame.KEYUP:
                if event.key in key_map:
                    btn = key_map[event.key]
                    memory_unit.release_button(btn)

        cycles_this_frame = 0
        while cycles_this_frame < CYCLES_PER_FRAME:
            cycles = cpu.step()
            cycles_this_frame += cycles

            ppu.step(cycles)
            
            div_counter += cycles
            if div_counter >= 256: 
                div_counter -= 256
                current_div = memory_unit.memory[0xFF04]
                memory_unit.memory[0xFF04] = (current_div + 1) & 0xFF
      
            if cycles == 0:
                cycles = 4
                cycles_this_frame += 4
                ppu.step(4)

        pygame.display.flip()
        clock.tick(60) # Mantém 60 FPS estáveis

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()