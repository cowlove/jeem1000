
import math
'''
/*
 * Tips for expanding this into a general running quadratic or linear least squares regression 
 * Based on 
 * http://mathforum.org/library/drmath/view/72047.html
 * 
 *  
 * maintain sums such that  
 * Sab  is sum of X^a*Y^b for each x,y in the data set. 
 * 
 * so when adding a point x,y with weight w
 * 
 *  S00 += 1 * w;
 *  S10 += x * w;
 *  S20 += x * x * w;
 *  S30 += x * x * x * w;
 *  S40 += x * x * x * x * w;
 *  S01 += y * w;
 *  S11 += x * y * w;
 *  S21 += x * x * y * w;
 *  S31 += x * x * x * y * w;
 *  S41 += x * x * x * x * y * w;
 * 
 *  Then the parameters a,b,c of the best fit equation y = ax^2 + bx + c
 *  are given by 
 *  
  a = (S01*S10*S30 - S11*S00*S30 - S01*S20*S20
       + S11*S10*S20 + S21*S00*S20 - S21*S10*S10)
    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20)

  b = (S11*S00*S40 - S01*S10*S40 + S01*S20*S30
       - S21*S00*S30 - S11*S20*S20 + S21*S10*S20)
    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20)

  c = (S01*S20*S40 - S11*S10*S40 - S01*S30*S30
       + S11*S20*S30 + S21*S10*S30 - S21*S20*S20)
    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20)
 
  
  and the parameters m and b of the best fit y = mx + b are given by 
  
  m = (S00 * S11 - S10 * S01) / (S00 * S20 - S10 * S10)
  b = (S01 - m * S10) / S00 
  
  and of course the average is given by 
  
  y = S01 / S00  (sum of y's divided by count)
  
  variance and sum of errors could probably also be computed from these sums, dunno

  Sum of Y offset errors should be:  a^2*S40 + (b^2 + 2ac)*S20 + c^2*S00 + S02 + 2ab*S30
     + 2bc*S10 - 2a*S21 - 2b*S11 - 2c*S01.
  
 */
'''
class RunningLeastSquares():
    
    def __init__(self, d, mc, ma):
        self.maxCount = mc
        self.maxAge = ma
        self.rmsErr = 0
        self.clear()
        self.hist = []
        
    
    def clear(self):
        self.S00 = self.S02 = self.S10 = self.S20 = self.S30 = self.S40 = self.S01 = self.S11 = self.S21 = self.S31 = self.S41 = 0.0
        self.coefficients = (0.0, 0.0, 0.0);
        self.lastX = 0.0;
        self.solved = False
        self.hist = []
    
    def isFull(self):
        return self.hist.__len__() == self.maxCount 
        
    def add(self, x, y, w = 1.0):
        self.lastX = x
        self.updateSums(x, y, w)
        self.hist.append((x,y,w))
        self.removeAged(self.lastX)

    def addY(self, y, w = 1.0):
        self.add(self.lastX + 1, y, w)

    def solve(self, degree):
        S00 = self.S00
        S01 = self.S01
        S02 = self.S02
        S10 = self.S10
        S20 = self.S20
        S30 = self.S30
        S40 = self.S40
        S11 = self.S11
        S21 = self.S21
        S31 = self.S31
        S41 = self.S41
         
        if (degree == 3): 
            a = ((S01*S10*S30 - S11*S00*S30 - S01*S20*S20
                    + S11*S10*S20 + S21*S00*S20 - S21*S10*S10)
                    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20))
    
            b = ((S11*S00*S40 - S01*S10*S40 + S01*S20*S30
                    - S21*S00*S30 - S11*S20*S20 + S21*S10*S20)
                    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20))
    
            c = ((S01*S20*S40 - S11*S10*S40 - S01*S30*S30
                    + S11*S20*S30 + S21*S10*S30 - S21*S20*S20)
                    /(S00*S20*S40 - S10*S10*S40 - S00*S30*S30 + 2*S10*S20*S30 - S20*S20*S20))
        elif (degree == 2): 
            a = 0;
            b = (S00 * S11 - S10 * S01) / (S00 * S20 - S10 * S10);
            c = (S01 - b * S10) / S00;
        elif (degree == 1): 
            a = b = 0;
            c = (S01 / S00);
        

        self.rmsErr = math.sqrt((a*a*S40 + (b*b + 2*a*c)*S20 + c*c*S00 + 
                S02 + 2*a*b*S30 + 2*b*c*S10 - 2*a*S21 - 2*b*S11 - 2*c*S01)/S00);
        
        
        self.coefficients = (c,b,a)
        self.solved = True;
    
    
    def updateSums(self, x, y, w):  
        self.S00 += 1 * w
        self.S01 += y * w
        self.S02 += y * y * w
        self.S10 += x * w
        self.S20 += x * x * w
        self.S11 += x * y * w
        self.S30 += x * x * x * w
        self.S40 += x * x * x * x * w
        self.S21 += x * x * y * w
        self.S31 += x * x * x * y * w
        self.S41 += x * x * x * x * y * w    
        self.solved = False;
    

    def removeAged(self, n): 
        while(self.hist.__len__() > 0 and ((self.maxCount > 0 and  self.hist.__len__() > self.maxCount) or 
            (self.maxAge > 0.0 and n - self.hist[0][0] > self.maxAge))):
            self.removeOldest();
    
    def removeOldest(self): 
        e = self.hist.pop(0);
        self.updateSums(e[0], e[1], -e[2])
    
    def rmsError(self, degree): 
        self.calculate(0, degree);
        return self.rmsErr

    def size(self): 
        return self.hist.__len__()
    
    def slope(self, x, deriv, degree):
        try:
            self.calculate(x, degree)
            y = 0.0
            for d in xrange(1, degree):
                v = math.pow(x, d - deriv) * self.coefficients[d]
                for i in xrange(0, deriv):
                    if (d - i > 0):
                        v *= (d - i)
                    else:
                        v = 0
                y += v
        except:
            y = 0.0
        return y

    
    def calculate(self, x, degree):
        try:
            if (self.hist.__len__() < 1):
                return 0;
            if (not self.solved):
                self.solve(degree)
            (c,b,a) = self.coefficients
            return a * x * x + b * x + c
        except:
            return 0
        
    
    def calculateY(self, degree): 
        return self.calculate(self.lastX, degree)
    
    
    '''
    public double lastX = 0.0, maxAge;
    public int maxCount;
    double S00, S02, S10, S20, S30, S40, S01, S11, S21, S31, S41;
    public ArrayList<Entry> hist = new ArrayList<Entry>();
    public double a,b,c; // coefficients for y = ax + b, y = axx + bx + c;
    double rmsErr;
    boolean solved;
    int degree;
    double []coefficients;
    public int getCount() {  return hist.size(); }
    '''
    