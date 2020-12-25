import pygame
from circshape import Limit, TextRenderCache, CircShape, TickSet, Arc
from colors import magenta,cyan,white,yellow,gold,green,skyblue,blue,red,ground,black,tan,dkyellow
from verticaltape import VerticalTape
from tach import GuageHistoryABC



class BoxedText():
    def __init__(self, sfc, pos, size, color):
        self.center = pos
        self.bg = sfc
        self.txtsize = size
        self.color = color
        
    def draw(self, txt):
        labelFont = pygame.font.Font(None, int(self.txtsize))        
        labelText = labelFont.render(txt, True, self.color, black)
        re = labelText.get_rect()
        re.center = self.center
        self.src.blit(labelText, re)
        pygame.draw.rect(self.bg, white, re, 1)


    
class HsiArc(CircShape,GuageHistoryABC):
    def __init__(self, w, center, radius):
        CircShape.__init__(self, center, radius)
        GuageHistoryABC.__init__(self)
        self.textCache = TextRenderCache()
        self.width = radius / 20
        self.interval = radius / 6
        self.arc = Arc((radius,radius), radius, (0, 360), 0, 0, self.width)
        self.tick1 = TickSet((radius,radius), radius, (0, 360), 10, self.interval, self.width / 2)
        self.tick2 = TickSet((radius,radius), radius, (0, 360), 5, self.interval / 2, self.width / 2)
        self.deg = 0
        self.window = w
        self.tsize = tsize = self.arc.radius / 20
        self.lastvalue = 0
        self.courseLine = 111
        self.track = 140
        self.gpsValid = False
        
        # draw a background surface to rotate        
        self.bg=pygame.surface.Surface((radius*2,radius*2),0,8)
        self.bg.set_colorkey((0,0,0))
        self.arc.window = self.tick1.window = self.tick2.window = self.bg
        self.tick1.start = self.tick2.start = 0
        self.tick1.end = self.tick2.end = 360
        pygame.draw.circle(self.bg, white, 
                           (self.arc.radius, self.arc.radius), 
                           self.arc.radius, self.width/2)
        for f in (self.tick1, self.tick2):
            f.draw(self.deg)
        cc = CircShape((radius,radius), radius)
        cc.window = self.bg
        cc.arrayText(((90, "N"), (60, "3"), (30, "6"), (270, "S"), (300, "15"), (330, "12")), 1, 0)        
        cc.arrayText(((0, "E"), (120, "33"), (150, "30"), (180, "W"), (210, "24"), (240, "21")), 1, 0)
 
        # draw a fixed foreground surface
        fgradius = radius * 1.1
        self.fg=pygame.surface.Surface((fgradius*2,fgradius*2),0,8)
        self.fg.set_colorkey((0,0,0))
        self.tick3 = TickSet((fgradius,fgradius), radius, (0, 360), 45, -self.interval / 2, self.width)
        self.tick4 = TickSet((fgradius,fgradius), radius, (70, 110), 10, -self.interval/2, self.width/2)
        fgc = CircShape((fgradius,fgradius),radius)
        fgc.window = self.fg
        self.tick3.window = self.tick4.window = self.fg
        self.tick3.draw(0)
        self.tick4.draw(0)
        triangle = ((tsize * 3,0), (tsize * 3, tsize * 2), (0, tsize))
        fgc.polyAtRadial(triangle, 90, radius, 1)
            
    def get_history(self, pt=False):
        return (self.history,)
    
    def get_rect(self):
        re = self.bg.get_rect()
        re.center = self.center
        return re

    def draw(self, force, noDraw):
        self.history.add(self.deg)
        if noDraw:
            return ()
        if int(self.lastvalue) == int(self.deg) and force == False:
            return ()
        
        self.lastvalue = self.deg
        s = pygame.transform.rotate(self.bg, self.deg)
        area = self.bg.get_rect()
        area.center = s.get_rect().center
        re = pygame.rect.Rect(area)
        re.center = self.center        
        self.window.blit(s, re, area)
        
        re = self.fg.get_rect()
        re.center = self.center
        self.window.blit(self.fg,re)
              
        width=int(self.width*.8)
        radius = self.arc.radius
        cldeg = 360 + 90 + self.deg - self.courseLine 
        bugdeg= 360 + 90 + self.deg - self.track
        
        self.polarLine((cldeg, radius * .4), (cldeg, radius*.85), magenta, width)
        self.polarLine((cldeg, -radius * .4), (cldeg, -radius*.85), magenta, width)
        self.polarLineOffset((cldeg, -radius * .4), (cldeg, +radius*.4), (cldeg + 90, radius*.1), magenta, width)

        tsize = self.tsize
        triangle = ((0,0), (0, tsize * 4), (tsize*3, tsize*2))
        self.polyAtRadial(triangle, cldeg, radius * .92, 1, magenta)
        self.polyAtRadial(triangle, bugdeg, radius*.92, 1, cyan if self.gpsValid else red)
        
        self.drawTxt()
        
        return (re,)
        
    def drawTxt(self):
        radius = self.arc.radius
        magenta=(255,100,255)
        cyan=(0,255,255)
        tsize = self.tsize
    
        #hdg=BoxedText(self.window, (center[0], center[1] - radius - tsize*2), radius*.3, white)
        #crs=BoxedText(self.window, (center[0], center[1] - radius - tsize*2), radius*.3, white)
        fs = int(radius * .27)

        labelText = self.textCache.text(("%03d" + chr(176)) % self.deg, fs*1.6)
        re = labelText.get_rect()
        re.centerx = self.center[0]
        re.top = self.center[1] - radius *.4 -tsize * 2
        self.window.blit(labelText, re)
        # pygame.draw.rect(self.window, white, re, 1)

        labelText = self.textCache.text(("TRK %03d" + chr(176)) % (self.track), 
                                        fs, cyan if self.gpsValid and self.track > 0 else red)
        re = labelText.get_rect()
        re.centerx = self.center[0] - radius *.8
        re.bottom = self.center[1] - radius*.8 -tsize * 2
        self.window.blit(labelText, re)
        #pygame.draw.rect(self.window, white, re, 1)
    
        labelText = self.textCache.text(("CRS %03d" + chr(176)) % (self.courseLine), fs, magenta)
        re = labelText.get_rect()
        re.centerx = self.center[0] + radius *.8
        re.bottom = self.center[1] - radius*.8 -tsize * 2
        self.window.blit(labelText, re)
        #pygame.draw.rect(self.window, white, re, 1)

        
    def random(self, span):
        self.deg += 1
        self.deg %= 360
        if (self.deg < 0):
            self.deg += 360
