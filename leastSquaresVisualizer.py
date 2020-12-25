from touchBox import *
from runningLeastSquares import *
from colors import *
from math import *

class LeastSquaresVisualizer(PushButtonBox):
    def __init__(self, window, r, rmsScale):
        PushButtonBox.__init__(self, window, r)
        self.ls = (RunningLeastSquares(1,0,60), RunningLeastSquares(1,0,30), RunningLeastSquares(1,0,10))
        self.startTime = datetime.datetime.now();
        self.fontSize = .8
        self.label = ""
        self.rmsScale = rmsScale
    
    def clear(self):
        for l in self.ls:
            l.clear()
        self.startTime = datetime.datetime.now();
            
            
    def add(self, v):
        now = (datetime.datetime.now() - self.startTime).total_seconds();
        for f in self.ls:
            f.add(now,v);
    
    def writeAt(self, x, t, color):
        fs = self.rec.height * self.fontSize
        txt = self.textCache.text(t, fs, color);
        re = txt.get_rect()
        re.top = self.rec.top + self.rec.height * .05;
        re.left = self.rec.left + self.rec.width * .05 + self.rec.height * x;
        self.w.blit(txt, re)
        
    def draw(self, force, noDraw):
        now = (datetime.datetime.now() - self.startTime).total_seconds();
        self.writeAt(0, self.label, blue)
        
        #self.writeAt(0, "%d" % (self.ls[0].hist[-1][1]/60), blue)
        for f in self.ls:
            val = f.slope(now, 1,2)
            err = f.rmsErr * self.rmsScale
            color = green
            if err > 100:
                color = yellow
            if err > 200:
                color = red
            self.writeAt(-1 + 2.2 * (self.ls.index(f) + 1), "%03.0f/%03.0f" % (math.fabs(val), err), color), 
        return (self.rec,)
           
    def pr(self):
        print self.str()
    
    def str(self):     
        rval = ""
        now = (datetime.datetime.now() - self.startTime).total_seconds();
        for f in self.ls:
            rval +=  "%03.0f/%03.01f  " % (f.slope(now,1,2), f.rmsErr)
        return rval
    
