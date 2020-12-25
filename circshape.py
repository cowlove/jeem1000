import pygame
import math
from colors import *

white=(255,255,255)

class Limit():
    def __init__(self, l, u, bc, tc, w):
        self.upper = u
        self.lower = l
        self.background = bc
        self.tapecolor = tc
        self.warn = w


class TextRenderCache():
    def __init__(self, color=white):
        self.fonts = {}
        self.color = color
        
    def text(self, text, fs, color=white):
        fs = int(fs)
        if self.fonts.has_key(fs) == False:
            font = pygame.font.Font(None, fs)
            self.fonts[fs] = FontRenderCache(font)
        return self.fonts[fs].text(text,color)


class FontRenderCache():
    def __init__(self, font):
        self.font = font
        self.chars = {}        
    
    def cachedChar(self, c, color):
        if self.chars.has_key((c,color)):
            return self.chars[(c,color)]
        s = self.font.render(c, True, color)
#        s.set_colorkey(self.colorkey)
        self.chars[(c,color)] = s
        return s
        
    def text(self, text,color=white):
        chars = ()
        w = 0
        h = 0
        for c in text:
            chars = chars + (self.cachedChar(c,color),)
        for s in chars:
            w += s.get_rect().width
            h = max(h, s.get_rect().height)
        rval = pygame.Surface((w,h))
        if color != black:
            colorkey = black
        else:
            colorkey = white
            rval.fill(colorkey)
        rval.set_colorkey(colorkey)
        w = 0
        for s in chars:
            rval.blit(s, (w,0,0,0))
            w += s.get_rect().width
        return rval

        
class CircShape():
    def __init__(self, center, radius,
                 arc=(0,0), interval=0, 
                 length=0, width=0):
        self.center = (int(center[0]), int(center[1]))
        self.radius = radius
        self.arc = arc
        self.interval = interval
        self.length = length
        self.width = width
        self.window = 0
        self.first = True
        self.textCache = TextRenderCache(white)

     
    def radial(self, deg, dist):
        return self.fromPt(self.center, deg, dist)
        
    def fromPt(self, start, deg, dist): 
        return (start[0] + dist * math.cos(math.radians(deg)), 
            start[1] - dist * math.sin(math.radians(deg)))
            
    def polarLine(self, p1, p2, color=white, width=1):
        self.polarLineOffset(p1, p2, (0,0), color, width)
        
    def polarLineOffset(self, p1, p2, offset, color=white, width=1):
        c1 = self.fromPt(self.center, p1[0], p1[1])
        c1 = self.fromPt(c1, offset[0], offset[1])
        c2 = self.fromPt(self.center, p2[0], p2[1])
        c2 = self.fromPt(c2, offset[0], offset[1])
        pygame.draw.line(self.window, color, c1, c2, width)
        
    def polyAtRadial(self, p, deg, r, rotate=1, color=white, width=0):
        s = self.polyToSfc(p, color, width)
        if (rotate):
            s = pygame.transform.rotate(s, deg)
        self.sfcAtRadial(deg, r, s)
        
    def polyToSfc(self, p, color=white, width=0):
        s=pygame.surface.Surface((100,100),0,8)
        s.set_colorkey((0,0,0))
        s.fill((0,0,0))
        re = pygame.draw.polygon(s, color, p, width)
        s2=pygame.surface.Surface((re[2], re[3]),0,8)
        s2.set_colorkey((0,0,0))
        s2.blit(s, (0,0), re)
        return s2
        
        
    def sfcAtRadial(self, deg, r, sfc, anchor=0):
        a = self.radial(deg, r)
        re = sfc.get_rect();
        if (anchor == 0):
            re.centerx = a[0]
        if (anchor < 0):
            re.left = a[0] - anchor
        if (anchor > 0):
            re.right = a[0] - anchor
        re.centery = a[1]
        self.window.blit(sfc, re)
    
        
    def text(self, deg, text, rotate=0, rad=0.75, fontsize=0.35,anchor=0):
        fs=int(fontsize*self.radius)

        s = self.textCache.text(text, fs)
        if (rotate):
            s = pygame.transform.rotate(s, deg - 90)
        self.sfcAtRadial(deg,  int(self.radius * rad), s, anchor)
        
    def arrayText(self, pts, rotate=0, offset=0):
        for p in pts:
            self.text(p[0] + offset, p[1], rotate)
            
        
class TickSet(CircShape):
    def __init__(self, center, radius, arc, interval, length, width):
        CircShape.__init__(self, center, radius, arc, interval, length, width)

    def drawOne(self, deg):
        pygame.draw.line(self.window, white, self.fromPt(self.center, deg, self.radius - self.length), 
            self.fromPt(self.center, deg, self.radius), self.width)

    def draw(self, offset=0):
        for d in xrange(self.arc[0], self.arc[1] + 1, self.interval):
            self.drawOne(d + offset)

class Arc(CircShape):
    def __init__(self, center, radius, arc, interval, length, width, color=white):
        CircShape.__init__(self, center, radius, arc, interval, length, width)
        self.deg = 0
        self.color=color
        
    def draw(self):
        for f in (0,.7,.2,.5,-.2):
            pygame.draw.arc(self.window, self.color, (self.center[0] - self.radius, self.center[1] - self.radius,
                         self.radius * 2, self.radius * 2),
                         math.radians(self.arc[0] + f), math.radians(self.arc[1] + 1 + f), self.width)

        
