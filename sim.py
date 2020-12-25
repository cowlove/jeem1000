import pygame
import time
import sys

pygame.init() 

#create the screen
mode=pygame.FULLSCREEN
#mode=0
window = pygame.display.set_mode((0,0), mode, 0) 
count = 0
while True:
    window.fill((0,0,0))
    pygame.draw.rect(window, (0,255,0), (0,0,100,100))
    pygame.display.flip()
    count = count + 1
    print "%d" % count
    for event in pygame.event.get(): 
        if True and (event.type == pygame.QUIT or event.type==pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN or count > 100):
            pygame.quit()
            sys.exit(0) 
    time.sleep(5)

