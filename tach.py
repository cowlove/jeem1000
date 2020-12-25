import pygame
from circshape import Limit, CircShape, TickSet, Arc
from colors import white,yellow,gold,green,skyblue,blue,red,ground,cyan,black,tan,dkyellow,magenta

import time
import math
import random
import os
import threading
import datetime

    
class GaugeAnnunciator:
    def __init__(self, title, threshold, timeout):
        self.title = title
        self.threshold = threshold
        self.timeout = timeout
        self.value = True
    

class GuageHistory:
    coloridx = 0
    colorchoices = (red,green,blue,tan,dkyellow,yellow,magenta,cyan,white,white,white,skyblue,magenta)
    def __init__(self, max_size  = 0, ra = False, histIntervalSeconds = 1):
        self.data = ();
        self.max_size = max_size
        self.range = ra
        self.changed = False
        if GuageHistory.coloridx < len(GuageHistory.colorchoices):
            self.color = GuageHistory.colorchoices[GuageHistory.coloridx]
            GuageHistory.coloridx += 1
        else:
            self.color = white
        self.value = False
        self.minmax = False;
        self.lastHistAdd = 0
        self.histIntervalSeconds = histIntervalSeconds
        self.maxHistorySize = 0
        self.annunciator = False
        self.annunciatorActive = False;
        
    def setAnnunciatorActive(self, active):
        self.annunciatorActive = active
        if active == True:
            self.annunciatorLastTime = datetime.datetime.now() - datetime.timedelta(seconds=1000)
            self.annunciatorLastTitleTime = datetime.datetime.now() - datetime.timedelta(seconds=1000)
        
    def add(self, v):
        if (time.time() - self.lastHistAdd > self.histIntervalSeconds):
            if (time.time() - self.lastHistAdd > self.histIntervalSeconds * 5):
                self.lastHistAdd = time.time();
            else:
                self.lastHistAdd += self.histIntervalSeconds
            self.data = (v,) + self.data;
            if len(self.data) > self.maxHistorySize:
                self.data = self.data[:self.maxHistorySize]
            self.changed = True
            if self.minmax == False:
                self.minmax=(v,v)
            self.minmax = (min(self.minmax[0], v), max(self.minmax[1], v))
        #if self.value:
        #    print len(self.data)
            
        if self.annunciator != False and self.annunciatorActive == True and self.annunciator.isReady():
            thresh = self.annunciatorThreshold
            if ((datetime.datetime.now() - self.annunciatorLastTime).total_seconds() > self.annunciatorTimeout 
                or int(v/thresh) != int(self.annunciatorLastValue/thresh)):
                #decreasing = v < self.annunciatorLastValue
                self.annunciatorLastTime = datetime.datetime.now()
                self.annunciatorLastValue = v
                v = v + self.annunciatorRound / 2
                v = v - (v % self.annunciatorRound)
                if (datetime.datetime.now() - self.annunciatorLastTitleTime).total_seconds() > self.annunciatorTimeout:
                    self.annunciatorLastTitleTime = datetime.datetime.now()
                    title = self.annunciatorTitle
                else:
                    title = ""
                self.annunciator.addAnnunciation(title + " %d" % v)
                
    def get(self):
        self.changed = False
        return self.data

class GuageHistoryABC:
    def __init__(self):
        self.history = GuageHistory()
    def get_history(self, pt=False):
        return (self.history,)
    def get_rect(self):
        return False
    def add(self, v):
        self.history.add(v)
    def isActive(self):
        return self.history.value
    def configureAnnunciator(self, annunc, title, threshold, round = 1, tmo = 15):
        self.history.annunciator = annunc
        self.history.annunciatorTitle = title
        self.history.annunciatorThreshold = threshold
        self.history.annunciatorRound = round
        self.history.annunciatorTimeout = tmo
        self.history.annunciatorActive = False
        self.history.annunciatorLastTime = 0
        self.history.annunciatorLastTitleTime = 0
        self.history.annunciatorLastValue = 0
        
class GuageArc(CircShape):
    def __init__(self, w, center, radius, fontsize, arc, rev):
        CircShape.__init__(self, center, radius)
        self.width = 3
        self.rev = rev
        tick = radius / 8
        self.bg = pygame.Surface((radius * 2, radius * 2),0,8)
        self.arc = Arc((radius,radius), radius, arc, 0, 0, self.width)
        self.tick1 = TickSet((radius,radius), radius, arc, arc[1] - arc[0], tick, self.width)
        self.tick1.window = self.arc.window = self.bg
        self.deg = 0
        self.window = w
        self.bg.set_colorkey((0,0,0))
        self.fgColor = white;
        self.needleLen = 1.0;
        
    def percentToDeg(self, pct):
        if self.rev == True:
            pct = 100 - pct
        return self.arc.arc[1] - (self.arc.arc[1] - self.arc.arc[0]) * pct / 100
       
    def drawbg(self):
        for f in ( self.arc, self.tick1):
            f.draw()
            
    def draw(self, drawBg = True):
        if self.window == False:
            return
			
        r = self.bg.get_rect()
        r.center = self.center
        if drawBg == True:
		    self.window.blit(self.bg,r)
        
        tsize = self.radius / 20
        diamond = ((tsize * 4,tsize), (tsize * 2, 0), (0, tsize), (tsize * 2, tsize * 2))
        self.polyAtRadial(diamond, self.deg, self.radius * self.needleLen - tsize * 3, 1, self.fgColor, 4)
        pygame.draw.line(self.window, self.fgColor, self.center, self.radial(self.deg, self.radius * .8), self.width)
        
   

class Tach(GuageArc,GuageHistoryABC):
    def __init__(self, w, center, radius, ra, arc=(-10,270),rev=False):
        GuageArc.__init__(self, w, center, radius, 0.5, arc, rev)
        GuageHistoryABC.__init__(self)
        self.value = 0;
        self.range = ra
        self.format = "%d"
        self.colors = ()
        self.textpos = 250
        self.textanchor = 0
        self.titletextpos = 270
        self.titletextanchor = 0
        self.title = ""
        self.lastvalue = 0
        self.drawn = False
        #elf.history = GuageHistory(1000, ra)
        self.fakeMotion = 0
        
    def drawbg(self):
        GuageArc.drawbg(self)
        for f in self.colors:
            f.draw()
        r = self.radius
        bgc = CircShape((r,r), r)
        bgc.window = self.bg
        bgc.text(self.titletextpos, self.title, 0, .65, 0.35, self.titletextanchor)
            
    def valueToDeg(self, v):
        p = float(v - self.range[0])/(self.range[1] - self.range[0]) * 100
        return self.percentToDeg(p)
    
    def addColor(self, lo, hi, color):
        r = self.radius
        if self.rev:
            x = hi
            hi = lo
            lo = x
        f = Arc((r,r), r * .90, (self.valueToDeg(hi), self.valueToDeg(lo)), 0, 0, self.width*3, color)
        f.window = self.bg
        self.colors = self.colors + (f,)
        self.drawbg()
#        self.arc3 = Arc((radius,radius), radius * .90, (self.arc.arc[0], self.percentToDeg(redline)), 0, 0, self.width*2, red)
#        self.arc2.window = self.arc3.window = self.bg

    #4.6 sec, w/ background 3.4sec, w/ no font .42sec          
    def draw(self, force, noDraw, drawBg = True):
        self.add(self.value)
        if noDraw or self.window == False:
            return ()
        
        if (self.drawn == False):
            self.drawbg()
        self.drawn = True
        
        if (self.fakeMotion != 0):
            change = self.fakeMotion * (self.range[1] - self.range[0]) * random.random()
            self.value += change
            if self.value > max(self.range) or self.value < min(self.range):
                self.value -= change
                self.fakeMotion *= -0.25
            self.fakeMotion += (random.random() - 0.5) * .01
            if (self.fakeMotion == 0):
                self.fakeMotion = 0.1
                
        if self.value != self.lastvalue or force:
            self.lastvalue = self.value
            self.deg = self.valueToDeg(self.value)
            self.text(self.textpos, self.format % self.value, 0, .35, 0.5,
                  self.textanchor)
            GuageArc.draw(self, drawBg)
            if self.history.value:
                pygame.draw.circle(self.window, self.history.color, self.center, 
                           int(self.radius * .1))
                
            return (self.get_rect(),)
        else:   
            return ()

        
    def get_rect(self):
        re = self.bg.get_rect()
        re.center = self.center
        return re
    
    def move(self, x):
        self.value += x
        if (self.value > self.max):
            self.value = 0;
        
    #ef get_history(self, pt=False):
    #   return (self.history, )


class TachPair(Tach):
    def __init__(self, w, center, radius, ra1, ra2, arc1 = (95,265), arc2 = (-85, 85)):
        Tach.__init__(self, w, center, radius, ra1, arc1)
        self.textpos = 260;
        self.textanchor = +1;
        self.titletextpos = 255
        self.titletextanchor = +1
        
        self.right=Tach(w, center, radius, ra2, arc2, True)
        self.right.textpos = 280;
        self.right.textanchor = -5;
        self.right.titletextpos = 285
        self.right.titletextanchor = -1
        
        self.select_together = True
        
    def draw(self, force, noDraw):
        rval = ()
        force = True # broken until we work out left/right portions
        self.right.fakeMotion = self.fakeMotion
        self.right.history.histIntervalSeconds = self.history.histIntervalSeconds
        self.right.history.maxHistorySize = self.history.maxHistorySize
        if Tach.draw(self, force, noDraw):
            re = self.get_rect()
            re.width /= 2
            re.right = self.center[0]
            rval = (re,)
        if self.right.draw(force, noDraw):
            re = self.right.get_rect()
            re.width /= 2
            re.left = self.right.center[0]
            rval += (re,)
        return rval   
    

    def get_history(self, pt=False):
        if pt != False and self.select_together == False:
            if pt[0] < self.center[0]:
                return (self.history,)
            else:
                return (self.right.history,)
        return (self.history, self.right.history)
        
        

class TachMultiple(Tach):
    def __init__(self, count, w, center , radius, ra, arc=(-10,270)):
        Tach.__init__(self, w, center, radius, ra, arc)
 
        self.tachs = ()
        colors = [red, green, blue]
        for c in range(1, count): 
			t = Tach(w, center, radius, ra, arc)
			t.fgColor = colors[c - 1]
			t.textpos = self.textpos + c * 80
			t.needleLen = (1.0 - .1 * c)
			self.tachs += (t,)
			
        self.select_together = True
   		
    def draw(self, force, noDraw):
        rval = () 
        force = True
        if Tach.draw(self, force, noDraw, True):
            re = self.get_rect()
            rval += (re,)
		
        for t in self.tachs:
            t.fakeMotion = self.fakeMotion
            t.history.histIntervalSeconds = self.history.histIntervalSeconds
            t.history.maxHistorySize = self.history.maxHistorySize
            if t.draw(force, noDraw, False):
                re = t.get_rect()
                rval += (re,)
        
        return rval   
    
    def get_history(self, pt=False):
        if pt != False and self.select_together == False:
            if pt[0] < self.center[0]:
                return (self.history,)
            else:
                return (self.history,)
        return (self.history,)
        

