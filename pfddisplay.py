import pygame
import math
import time

from colors import white,yellow,gold,green,skyblue,blue,red,ground,black,tan,dkyellow
from circshape import Limit, CircShape, TickSet, Arc
from colors import white,yellow,gold,green,skyblue,blue,red,ground,black,tan,dkyellow
from verticaltape import VerticalTape
from runningLeastSquares import RunningLeastSquares

            
class PfdDisplay(CircShape):
    def __init__(self, w, center, radius):
        CircShape.__init__(self, center, radius)
        width = 3
        tick = radius / 8
        center = (radius, radius)
        # Arc and ticks for AI, from 30 to 150 degrees
        self.arc = Arc( center, radius *.95, (30, 150), 0, 0, width)
        self.tick1 = TickSet(center, radius *.95, (60, 120), 10, -tick / 2, width)
        self.tick2 = TickSet(center, radius * .95, (45, 135), 45, -tick / 2, width)
        self.tick3 = TickSet(center, radius * .95, (30, 150), 30, -tick, width)
        self.deg = self.oat = 0
        self.window = w
        self.width = width
        self.pitch = self.yaw = self.groundSpeed = self.slope = 0.0
        self.gpsValid = False
        self.deg = self.tas = self.densityAlt = 0
     
        h=self.radius *1.5
        w=self.radius*.44
        self.vt1=VerticalTape((self.center[0] - w*2.5 - w, self.center[1] - h * .6), w, h, (0,110),50,5)
        self.vt1.addColorRange(44,70,green,.20)
        self.vt1.addColorRange(35,60,white,.10)
        self.vt1.addColorRange(70,90,yellow,.20)
        self.vt1.addColorRange(90,91,red,2)
        self.vt1.slew = .02
        self.vt1.rateDisplay.trendLabel = False
        self.vt1.rateDisplay.trendPeriod = 15
        
        self.vt2=VerticalTape((self.center[0] + w*2.5, self.center[1] - h * .6), w*1.1, h, (-500,10000), 500, 20)
        self.vt2.left = 0
        self.vt2.majorticks=5
        self.vt2.textsize=.46
        self.vt2.setRollPart(20)
        self.vt2.slew = .005
        self.vt2.history.range = False
        self.vt2.rateDisplay.trendLabel = True
        self.vt2.rateDisplay.trendPeriod = 15
        self.vt2.rateDisplay.trendProjection = 60
        self.override = 0;

        self.htick = htick = 0.18 * self.radius;  # equivalent of 5 degrees of horizon
        
        # Make a background surface for all rotatable stuff 
        backsize=self.radius * 2
        bg=pygame.surface.Surface((backsize, backsize),pygame.SRCALPHA, 16)
        bg.fill((0,0,0,0))
        bgc = CircShape((backsize/2, backsize/2), backsize/2)
        bgc.window = bg
        re = bg.get_rect()
        re.top = backsize / 2 + htick * self.pitch / 5
        re.height = backsize - re.top;
        self.arc.window = self.tick1.window = self.tick2.window = self.tick3.window = bg
        self.arc.draw()
        for f in (self.tick1, self.tick2, self.tick3):
            f.draw(0)

        # Draw horizon lines
        for p in (-4, -2, 0, 2, 4):
            pygame.draw.line(bg, white, (backsize / 2 + self.radius * .30, backsize / 2 + p * htick), 
                         (backsize / 2 - self.radius * .3, backsize / 2 +  p * htick ), self.width)
        for p in (-3,-1,1,3):
            pygame.draw.line(bg, white, (backsize / 2 + self.radius * .15, backsize / 2  + p * htick), 
                         (backsize / 2 - self.radius * .15, backsize / 2  + htick * p ), self.width)
        sz=self.radius * .05
        ptrsize=htick * .7
        p = ((0,sz),(sz,0),(sz,sz*2))
        p = ((0,ptrsize / 2), (ptrsize, 0), (ptrsize, ptrsize))
        bgc.polyAtRadial(p, 90 + self.deg, self.radius,1,white)
        
        
        # not smart enough to rotate a clipped,bounded surface yet, get the whole background rect
        # could work if we just make sure the bounded rect is symmtric around both x and y axis
        #r = bg.get_bounding_rect()  
        origr = bg.get_rect()
        r = bg.get_bounding_rect()
        w = max(origr.center[0] - r.left, r.right - origr.center[0]) * 2
        h = max(origr.center[1] - r.top, r.bottom - origr.center[1]) * 2
        r = pygame.rect.Rect(0,0,w,h)
        r.center = origr.center
        self.bg=pygame.surface.Surface((r.width,r.height),0,8)
        self.bg.set_colorkey((0,0,0))
        self.bg.blit(bg, pygame.rect.Rect(0,0,0,0), r)

        
        # And another surface for the non-rotating parts (2.912 at start, 2.106 when done)
        # Bank and yaw pointers
        fg=pygame.surface.Surface((backsize, backsize),pygame.SRCALPHA, 16)
        #fg.set_colorkey((0,0,0))
        fg.fill((0,0,0,0))
        fgc = CircShape((backsize/2, backsize/2), backsize/2)
        fgc.window = fg
        
        p = ((0,ptrsize / 2), (ptrsize, 0), (ptrsize, ptrsize))
        fgc.polyAtRadial(p, 270, -self.radius * .88,1,yellow)
        p = ((0,0),(0,ptrsize), (ptrsize/2, ptrsize), (ptrsize/2,0))
        fgc.polyAtRadial(p, 270 + self.yaw, -self.radius * .77,1,yellow)
 
        # Yellow recticles
        p = ((0,0), (sz*8, sz), (0,sz*2))
        fgc.polyAtRadial(p, 0, -self.radius *.5,1, yellow)
        fgc.polyAtRadial(p, 180, -self.radius *.5,1, yellow)
        p = ((0,sz),(sz,0),(sz,sz*2))
        fgc.polyAtRadial(p, 270, self.radius *.05,1, yellow)
        pygame.draw.circle(fg, yellow, fgc.center, int(fgc.radius * .02), 0 )
        
        # Trim fg down, move it over to reflect asymmetric trimming
        r = fg.get_bounding_rect()  
        self.fg=pygame.surface.Surface((r.width,r.height),0,8)
        self.fg.set_colorkey((0,0,0))
        self.fg.blit(fg, pygame.rect.Rect(0,0,0,0), r)
        
        self.fgloc = self.fg.get_rect()
        self.fgloc.left = self.center[0] - fg.get_rect().width / 2 + r.left
        self.fgloc.top = self.center[1] - fg.get_rect().height / 2 + r.top
        
        

    # given a rect and two points on the sides of the rect, return a poly
    # that outlines the half of the rectangle divided by those points. 
    # (Follow the points in a clockwise fashion)        
    def divideRect(self, rec, p1, p2):
        if p1[1] > rec.bottom and p2[1] > rec.bottom:
            return (rec.topleft,rec.topright,rec.bottomright,rec.bottomleft)
        if p1[1] < rec.top and p2[1] < rec.top:
            return ()
        
        rval = (p1, p2)
        corners=(rec.topleft, rec.topright, rec.bottomright, rec.bottomleft)
        for f in corners:
            if (f[0] == p1[0] and f[1] == p2[1]) or (f[1] == p1[1] and f[0] == p2[0]):
                return rval + (f,)
        
        if p2[0] == rec.right:
            return rval + (rec.bottomright, rec.bottomleft)
        if p2[0] == rec.left:
            return rval + (rec.topleft, rec.topright)
        if p2[1] == rec.top:
            return rval + (rec.topright, rec.bottomright)
        return rval + (rec.bottomleft, rec.topleft)
        
    # Find the intercept point between a rectangle and a line
    # defined by a point in the rectangle and a degree
    def lineRectInterceptRadius(self, rec, pt, deg):
        deg = (deg + 360) % 360
        if (deg == 90):
            return (pt[0], rec.top)
        if (deg == 0):
            return (rec.right, pt[1])
        if (deg == 180):
            return (rec.left, pt[1])
        if (deg == 270):
            return (pt[0], rec.bottom)
        if (deg < 180):
            y = rec.top
        else:
            y = rec.bottom
        if (deg > 90 and deg < 270):
            x = rec.left
        else:
            x = rec.right
        py = pt[1] - (x - pt[0]) * math.tan(math.radians(deg))
        if (math.fabs(py - pt[1]) < math.fabs(y - pt[1])):
            return (x, py)
        px = pt[0] + (y - pt[1]) * math.tan(math.radians(deg - 90))
        return (px, y)
    
    def draw(self, force, noDraw):
    #    self.deg = self.override
    #    self.override = (self.override + 1 % 360)
    
        rval = ()
        if noDraw == False:
            area = pygame.Rect(0, 0, self.radius * 3.5, self.radius * 2.2);
            r = pygame.Rect(area)
            r.center = (self.center[0] + self.radius * .2, self.center[1] - self.radius * .30)
            rval = (r,)
            
            # Draw sky/ground into window        
            horiz=(self.center[0],self.center[1] + self.pitch * self.htick / 5)
            p1 = self.lineRectInterceptRadius(r, horiz, self.deg)
            p2 = self.lineRectInterceptRadius(r, horiz, self.deg + 180)
            
            pygame.draw.rect(self.window, skyblue, r, 0)
            pol=self.divideRect(r, p2, p1)
            if len(pol) > 2:
                pygame.draw.polygon(self.window,ground,pol,0)
                #pygame.draw.line(self.window, yellow, p1, p2, self.width)
                
            # rotate and blit the predrawn display         
            s = pygame.transform.rotate(self.bg, self.deg)
            r = s.get_rect()
            r.center = self.center;
            self.window.blit(s, r)
                
            
            self.window.blit(self.fg, self.fgloc)
            #pygame.draw.rect(self.window, white, self.fgloc, 1)
                      
            labelText = self.textCache.text("GS %d"  %  self.groundSpeed, self.radius * .3, white)
            if not self.gpsValid:
                pygame.draw.line(labelText, red, (0,labelText.get_rect().center[1]), 
                                    (labelText.get_rect().width, labelText.get_rect().center[1]), 3)
            re = labelText.get_rect()
            re.center = self.center
            re.left = self.center[0] - self.radius * 1.55
            re.top = self.center[1] + self.radius * .57  
            self.window.blit(labelText, re)
    
            labelText = self.textCache.text("OAT %d"  %  self.oat, self.radius * .3, white)
            re = labelText.get_rect()
            re.center = self.center
            re.left = self.center[0] - self.radius * 0.2
            re.top = self.center[1] + self.radius * .57  
            self.window.blit(labelText, re)

            
            labelText = self.textCache.text("TAS %d"  %  self.tas, self.radius * .3, white)
            re = labelText.get_rect()
            re.center = self.center
            re.left = self.center[0] - self.radius * 1.55
            re.top = self.center[1] - self.radius * 1.12
            self.window.blit(labelText, re)
        
            labelText = self.textCache.text("DA %d"  %  self.densityAlt, self.radius * .3, white)
            re = labelText.get_rect()
            re.center = self.center
            re.left = self.center[0] + self.radius * 1.1
            re.top = self.center[1] - self.radius * 1.12 
            self.window.blit(labelText, re)
    
            if abs(self.slope) > .01:
                txt = "GL %.2f"  %  abs(1000 / self.slope / 5280)
            else:
                txt = "GL -"
            labelText = self.textCache.text(txt, self.radius * .3, white)
            re = labelText.get_rect()
            re.center = self.center
            re.left = self.center[0] + self.radius * 1.1
            re.top = self.center[1] + self.radius * .57  
            self.window.blit(labelText, re)
    
        self.vt1.draw(self.window, noDraw)
        self.vt2.draw(self.window, noDraw)

        return rval
        
    
      
