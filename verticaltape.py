import pygame
from colors import white,black,yellow,magenta
import circshape
import math
import time
import runningLeastSquares
from tach import GuageHistoryABC

class TextRoll():
    def __init__(self, incr, fs):
        self.fontsize = fs
        self.incr = incr
        self.textCache = circshape.TextRenderCache()

        chars = len("%d" % incr)
        self.limit = int(math.pow(10,chars))

        lines = ()
        fmt = "%0" + ("%d" % chars) + "d"
        for x in  [incr, 0,] + range(self.limit - incr, -1, -incr):
            lines += (self.textCache.text((fmt % x)[-chars:], fs, yellow),)
        lines += (lines[1],)    
               
        s = pygame.Surface((lines[0].get_rect().width, lines[0].get_rect().height * len(lines)), 0, 8)
        r = pygame.rect.Rect(0,0,0,0)
        for l in lines:
            s.blit(l, r)
            r.top += fs*.52
  
        self.usableRange = (fs*.52*1.8, fs*(float(len(lines))-1.5)*.52)
        self.sfc = s
        self.width = lines[0].get_rect().width
        
    def getTextRollWindow(self,v, sfc, rec):
        y = (1.0 - float(v%self.limit) / self.limit) * (self.usableRange[1] - self.usableRange[0]) + self.usableRange[0]
        area = pygame.rect.Rect(rec)
        area.left = 0
        area.centery = y
        
        sfc.blit(self.sfc, rec, area)
        
        
            
    
class RateDisplay(GuageHistoryABC):
    def __init__(self, vt, width, period, label):
        GuageHistoryABC.__init__(self)
        self.history.color = magenta
        self.center = vt.center
        self.vt = vt
        self.center = (self.center[0] + vt.width, self.center[1])
        self.width = width
        self.height = vt.height
        self.linew = vt.linew
        self.startTime = time.time()
        self.trendPeriod = period
        self.trendProjection = period
        self.trendLabel = label
        self.rateSolver = runningLeastSquares.RunningLeastSquares(1, 0, 30)
        self.value = 0
        self.textsize = vt.textsize
        self.textCache = circshape.TextRenderCache()
        self.rec = pygame.Rect(0, 0, self.width, self.height)
        self.rec.topleft = self.center

    def get_rect(self):
        return self.rec
      
    def get_history(self, pt=False):
        return (self.history, )
 
    def draw(self, win, noDraw):
        h = self.height
        w = self.width
        # draw trend line and value
        now = time.time() - self.startTime
        self.rateSolver.add(now, self.vt.value)
        self.value =  self.rateSolver.slope(now, 1, 2) * self.trendProjection 
        self.history.add(self.value)
        
        if noDraw:
            return ()
        
        vs = self.value - (self.value % 10)
        y = -min(h/2, max(vs, -h/2)) 
        pygame.draw.rect(win, magenta, (self.center[0], self.center[1] + h*.5, 5, y), 0)

        if self.trendLabel:
            y = min(h/2.3, max(y, -h/2.3)) # further constrain the vert pos of label box to avoid text collision
            labelText = self.textCache.text("%d"  %  math.fabs(vs), w * self.textsize, white)
            re = labelText.get_rect()
            re.center = (0, self.center[1] + h*.5 + y)  
            re.left = self.center[0] + w *.1
            pt = (self.center[0] + w * .05, self.center[1] + h*.5 + y)
            poly = (pt, (re.left, re.top), (re.right, re.top), (re.right, re.bottom), 
                                               (re.left, re.bottom), pt)
            pygame.draw.polygon(win, black, poly, 0)
            pygame.draw.polygon(win, magenta, poly, self.linew)
            win.blit(labelText, re)

        if (self.history.value):
            sz = int(w * .15)
            dot = (re.left + sz/2, re.top - sz)
            pygame.draw.circle(win, self.history.color, dot, int(sz * .75))
            pygame.draw.circle(win, white, dot, int(sz * .75), sz / 5)

        return (pygame.rect.Rect(self.center[0], self.center[1], w, h),)
        
class VerticalTape(GuageHistoryABC):
    def __init__(self, c, w, h, span=(0,120), scale=50, ticks=5):
        GuageHistoryABC.__init__(self)
        self.center = c
        self.width = w
        self.height = h
        self.linew = 3
        self.left =1
        self.value = 10
        self.lastvalue = 0
        self.scale = scale
        self.ticks=ticks
        self.slew = .01
        self.span = span;
        self.majorticks=2
        #self.rollpart = 1 # portion of the value text that is a rolling tape 
        self.textsize = 0.55
        self.textCache = circshape.TextRenderCache()
        self.backgroundDone = False
        self.bh = int(float(span[1] - span[0])/scale*h)
        self.pixPerUnit = float(self.bh)/(span[1] - span[0])
        self.background = pygame.Surface((w,self.bh),0,8)
        self.background.fill((0,0,0))
        self.background.set_colorkey((0,0,0))
        self.setRollPart(1)
        self.rec = pygame.Rect(0, 0, w, h)
        self.rec.topleft = c
        
        self.rateDisplay = RateDisplay(self, self.width, 60, True)
        
    def get_history(self, pt=False):
        return (self.history, )
    
    def get_rect(self):
        return self.rec
      
    def setRollPart(self, x):
        self.rollpart = x
        self.textRoll = TextRoll(self.rollpart,self.textsize * self.width)
        
    def text(self, s, text, x, y, size, c=white): 
            sfc = self.textCache.text(text, size, c)
            r=sfc.get_rect()
            r.right=x
            r.centery=y
            s.blit(sfc, r)
         
    def addColorRange(self, lo, hi, color, w):
        lo = self.valToPixel(lo)
        hi = self.valToPixel(hi)
        pygame.draw.line(self.background, color, 
                         (self.width*(1-w/2),lo),
                         (self.width*(1-w/2),hi), 
                         int(self.width*w))

    def valToPixel(self, y):
        return self.bh - y * self.pixPerUnit
        

    def drawBackground(self):
        w = self.width
        s = self.background
        self.backgroundDone = True
        for f in xrange(self.span[0], self.span[1], self.ticks):
            y = self.valToPixel(f)
            pygame.draw.line(s, white, (w*.85, y), (w*1.0, y), self.linew)
        for f in xrange(self.span[0], self.span[1], self.ticks * self.majorticks):
            y = self.valToPixel(f)
            pygame.draw.line(s, white, (w*.75, y), (w*1.0, y), self.linew)
            self.text(s, "%d" % f, w*.72, y, w*.45)
            

    def draw(self, win, noDraw):
        #if int(self.lastvalue) == int(self.value):
        #   return ()
        self.history.add(self.value);
        r1 = self.rateDisplay.draw(win, noDraw)    
        if noDraw:
            return ()

        self.lastvalue = self.value
        w=self.width
        h=self.height
        #dim the area
        s=pygame.surface.Surface((int(w),int(h)),0,8)
        s.set_alpha(100)
        win.blit(s, pygame.Rect(self.center[0], self.center[1], 0, 0))

        # now use the surface to build our guage
        s=pygame.surface.Surface((int(w),int(h)),0,8)
        s.fill((255,0,0))
        s.set_colorkey((255,0,0))
        if (self.backgroundDone == False):
            self.drawBackground()
        s.blit(self.background, (0,0,0,0),
               (0,self.valToPixel(self.value) - h / 2, w, h))
        pygame.draw.rect(s, white, (0, 0, w, h), self.linew)
        # Todo- these should be scaled with self.textsize*w
        pygame.draw.polygon(s, black, ((w*.1,h*.45),(w*.5,h*.45),(w*.5,h*.42),(w*.8,h*.42),
                                            (w*.8,h*.45),(w*.98,h*.5),(w*.8,h*.55),
                                            (w*.8,h*.58),(w*.5,h*.58),(w*.5,h*.55),
                                            (w*.1,h*.55)), 0)
        
        #if (self.left == 0):
        #1    s = pygame.transform.rotate(s, 180)
        dispvalue = self.value
        if self.rollpart > 0 and (dispvalue % self.textRoll.limit) > self.textRoll.limit - self.textRoll.incr /  2:
            dispvalue =  (dispvalue + self.textRoll.incr / 2) 
        else:
            dispvalue = self.value
        
        self.text(s, "% 4d" % dispvalue, w*.8, h*.5, w*self.textsize, yellow)
  
        if (self.history.value):
            sz = int(w * .15)
            pygame.draw.circle(s, self.history.color, (sz,sz), int(sz * .75))
            pygame.draw.circle(s, white, (sz,sz), int(sz * .75), sz / 5)
        #pygame.draw.circle
        rollbox = pygame.rect.Rect(0,0,self.textRoll.width,w*.5)
        rollbox.centery = h*.5
        rollbox.left=w*.8-self.textRoll.width
        self.textRoll.getTextRollWindow(self.value, s, rollbox)
        win.blit(s, pygame.Rect(self.center[0], self.center[1], 0, 0))
        
        self.value += self.slew * self.scale / 20
        if (self.value > self.span[1] or self.value < self.span[0]):
            self.slew *= -1 
            
        
        return (r1, pygame.rect.Rect(self.center[0], self.center[1], w, h),)