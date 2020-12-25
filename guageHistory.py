from touchBox import * 

class GuageHistoryDisplay(Box, TouchHandler):
    def __init__(self, wind, r):
        Box.__init__(self, wind, r)
        TouchHandler.__init__(self)
        self.guages = ();
        self.scaleIndex = 0
        self.textCache = TextRenderCache(white)
        self.intervalSec = 60.0 / (self.rec.width - self.thickness * 2)
        self.maxHistorySize = int(GuageHistoryDisplay.ScaleOptions[len(GuageHistoryDisplay.ScaleOptions) - 1] * 60.0 / self.intervalSec)
        self.selectModeAnnounce = False
        
    def addOtherTouchable(self, obj):
        TouchHandler.add(self, obj.get_rect(), obj)
        
    def addGuage(self, guage):
        TouchHandler.add(self, guage.get_rect(), TouchActionSelectGuageHistory(guage, self))
        guage.history.histIntervalSeconds = self.intervalSec
        guage.history.maxHistorySize = self.maxHistorySize
        self.guages += (guage,);

    ScaleOptions = (1,5,15,60)
    #ScaleOptions = (1,2)
    
    def onTouch(self, isLong, point):
        self.scaleIndex += 1
        if (self.scaleIndex >= len(GuageHistoryDisplay.ScaleOptions)):
            self.scaleIndex = 0
    
    def selectGuage(self, guage, islong, pt):
        if self.selectModeAnnounce == True and not self.isAnnunciatorSelected():
            self.clearAnnunciator()
            for h in guage.get_history(pt):
                h.setAnnunciatorActive(True)
        else:
            if islong:    # Clear all guages on a long touch
                for g in self.guages:
                    for h in g.get_history():
                        h.value = False 
            for h in guage.get_history(pt):
                h.value = not h.value

    def setAnnunciatorMode(self, mode):
        self.selectModeAnnounce = mode
        self.clearAnnunciator()
                    
    def clearAnnunciator(self):
        for g in self.guages:
            for h in g.get_history():
                h.annunciatorActive = False

    def isAnnunciatorSelected(self):
        for g in self.guages:
            for h in g.get_history():
                if h.annunciatorActive:
                    return True
        return False
    
    def get_history(self, pt=False):
        return ()
    
    def draw(self, force, noDraw):
        if noDraw:
            return
        
        for g in self.guages:
            for h in g.get_history():
                if h.changed:
                    force = True
                
        Box.draw(self, force, False)
        
        minutes = GuageHistoryDisplay.ScaleOptions[self.scaleIndex];
        fs = self.rec.width * .10
        txt = self.textCache.text("%d min" % minutes, fs, (100,100,100));
        re = txt.get_rect()
        re.top = self.rec.bottom - self.rec.height * .32;
        re.left = self.rec.left + self.rec.width * .02;
        self.w.blit(txt, re)
        
        scale = max(1, minutes)
            
        if (force):
            for g in self.guages:
                for h in g.get_history():
                    if h.value:
                        ra = h.range
                        #if ra == False:
                        ra = h.minmax
                        x = self.rec.right
                        lastpt = (0,0)
                        seconds = 0
                        total = 0.0
                        for d in h.get():
                            total += d
                            seconds += 1
                            if seconds % scale == 0:
                                y = 0
                                if (scale != 0 and ra[1] - ra[0] != 0):
                                    y = self.rec.bottom - self.thickness - (1.0 * total / scale - ra[0]) / (ra[1] - ra[0]) * (self.rec.height - self.thickness * 2)
                                y = max(y, self.rec.top + self.thickness)
                                y = min(y, self.rec.bottom - self.thickness)
                                pt = (x,y)
                                if (x != self.rec.right):
                                    pygame.draw.line(self.w, h.color, lastpt, pt, 2)
                                lastpt = pt
                                x -= 1
                                total = 0.0
                                if (x < self.rec.left):
                                    break
            return (self.rec,)
        return ()
                       
        
class TouchActionSelectGuageHistory():
    def __init__(self, guage, history):
        self.guage = guage
        self.hxBox = history
        
    def onTouch(self, islong, point):
        self.hxBox.selectGuage(self.guage, islong, point)
        
        
