import pygame
from circshape import Limit, CircShape, TickSet, Arc
from colors import white,yellow,gold,green,skyblue,blue,red,ground,black,tan,dkyellow
from verticaltape import VerticalTape


import random

     
     
class HorizontalTape():
    def __init__(self, window, text, fmt, x, y, mi, ma):
        self.fmt=fmt
        self.border=white
        self.window = window
        self.border_thickness=3
        self.width=230
        self.fill = green
        self.height=50
        self.xstart=150 + x
        self.ystart=y
        self.value=6300
        self.valueMin=mi
        self.valueMax=ma
        self.label = text;
        self.limits = []
        
    def addlimit(self, l):
        if l.upper > self.valueMax:
            l.upper = self.valueMax;
        if l.lower < self.valueMin:
            l.lower = self.valueMin    
        self.limits.append(l)
        
    def set(self, v):
        if (v < self.valueMin):
            v = self.valueMin
        if ( v > self.valueMax):
            v = self.valueMax
        self.value = v
        self.draw()

    def random(self, percent):
        span=(self.valueMax - self.valueMin) * percent / 100;
        self.set(self.value + (random.random() - 0.5) * span)
        
    def getx(self, v):
        return self.border_thickness + (self.width - self.border_thickness * 2) * (v - self.valueMin) / (self.valueMax - self.valueMin) 
                
    def draw(self):
        color = green
        for l in self.limits:
            if self.value >= l.lower and self.value <= l.upper:
                color = l.tapecolor
        p = (self.xstart + self.getx(self.value), self.ystart + self.height - self.border_thickness * 2 - 2)
        
        pygame.draw.rect(self.window, self.border, (self.xstart,self.ystart,self.width, self.height), self.border_thickness)
        y = self.ystart + 43

        for l in self.limits:       
            pygame.draw.line(self.window, l.background, 
                (self.xstart + self.border_thickness + (self.width - self.border_thickness * 2) * (l.lower - self.valueMin) / (self.valueMax - self.valueMin), y), 
                (self.xstart + self.border_thickness + (self.width - self.border_thickness * 2) * (l.upper - self.valueMin) / (self.valueMax - self.valueMin), y), 
                10)
                
        tthick=10
        pl=((p[0], p[1]), (p[0] - tthick, p[1] - self.height / 2), (p[0] + tthick, p[1] - self.height / 2))
        pygame.draw.polygon(self.window, color, pl, 0)
        pygame.draw.polygon(self.window, white, pl, 3)


        labelFont = pygame.font.Font(None, 45)        
        labelText = labelFont.render(self.label, False, white, black)
        labelText.set_colorkey(black)
        self.window.blit(labelText, (self.xstart - 110,self.ystart ))
        labelText = labelFont.render(self.fmt % self.value, False, white, black)
        labelText.set_colorkey(black)
        self.window.blit(labelText, (self.xstart + 15,self.ystart ))



guages=[]
def make_gauges():
    #BROKEN CODE
    window =1 
    
    rpm=HorizontalTape(window, 'RPM', '%d', 0, 0, 8000)
    rpm.addlimit(Limit(6000,9999, red, red, False))
    rpm.addlimit(Limit(5500,6000, yellow, dkyellow, False))
    rpm.addlimit(Limit(2000,5500, green, green, False))
    fflow=HorizontalTape(window, 'FFLOW', '%.1f', 60, 0.0, 10.0)
    fflow.addlimit(Limit(2.0, 6.8, green, green, False))
    fflow.addlimit(Limit(0, 2.0, red, red, False))
    fflow.addlimit(Limit(6.8, 9999, red, red, False))
    
    fpres=HorizontalTape(window, 'FPRES', '%.1f', 120, 0.0, 7.0)
    fpres.addlimit(Limit(1.0, 5.0, green, green, False))
    fpres.addlimit(Limit(0, 1.0, red, red, False))
    fpres.addlimit(Limit(5.0, 9999, yellow, dkyellow, False))
    
    egt1=HorizontalTape(window, 'EGT1', '%d', 180, 600, 1400)
    egt1.addlimit(Limit(800, 1100, green, green, False))
    egt1.addlimit(Limit(1100, 1150, yellow, dkyellow, False))
    egt1.addlimit(Limit(1150, 9999, red, red, False))
    
    egt2=HorizontalTape(window, 'EGT2', '%d', 240, 600, 1400)
    egt2.addlimit(Limit(800, 1100, green, green, False))
    egt2.addlimit(Limit(1100, 1150, yellow, dkyellow, False))
    egt2.addlimit(Limit(1150, 9999, red, red, False))
    
    cht=HorizontalTape(window, 'CHT', '%d', 300, 100, 250)
    cht.addlimit(Limit(120, 195, green, green, False))
    cht.addlimit(Limit(195, 205, yellow, dkyellow, False))
    cht.addlimit(Limit(205, 9999, red, red, False))
    
    mapr=HorizontalTape(window, 'MAP', '%.1f', 360, 0.0, 32.0)
    
    amps=HorizontalTape(window, 'AMPS', '%+.1f', 420, -50, +50.0)
    amps.addlimit(Limit(0,15, green, green, False))
    amps.addlimit(Limit(15,999, yellow, dkyellow, False))
    amps.addlimit(Limit(-999, 0, red, red, False))
    
    volts=HorizontalTape(window, 'VOLTS', '%.1f', 480, 9, 18.0)
    volts.addlimit(Limit(11.8,14.5, green, green, False))
    volts.addlimit(Limit(0,11.8, red, red, False))
    volts.addlimit(Limit(14.5,999, yellow, dkyellow, False))
    
    rpm.set(6100)
    fflow.set(4.8)
    fpres.set(2.0)
    egt1.set(990)
    egt2.set(1010)
    cht.set(180)
    mapr.set(25)
    amps.set(-10)
    volts.set(12.1)
    
    
    
    guages.append(rpm)
    guages.append(fflow)
    guages.append(fpres)
    guages.append(egt1)
    guages.append(egt2)
    guages.append(cht)
    guages.append(mapr)
    guages.append(volts)
    guages.append(amps)
    

    