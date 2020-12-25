import time

class RollingAverage():
    def __init__(self, s):
        self.size = s
        self.sum = 0.0
        self.hist = []
        self.count = 0;
        
    def clear(self):
        self.count = self.sum = 0
        self.hist.clear()
        
    def add(self,v):
        if (self.count == self.size):
            self.sum -= self.hist.pop(0)
            self.count -= 1
        self.count += 1
        self.hist.append(v)
        self.sum += v
        
    def average(self):
        if (self.count > 0):
            return self.sum / self.count
        return 0
    
class RateTimer():
    def __init__(self, size=20):
        self.last=0
        self.avg = RollingAverage(size)
    def rate(self):
        
        now = int(round(time.time() * 1000))
        elapsed = now - self.last
        if (elapsed == 0 or self.last == 0):
            self.last = now
            return 0
        self.last = now
        self.avg.add(1000/elapsed)
        return self.avg.average()
    
        
