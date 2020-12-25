'''
Created on Oct 19, 2013

@author: jim
'''
from ratetimer import RollingAverage
import time
import threading
import math
from loggingObject import LoggingObject
from __builtin__ import False

class FakeValues():
    def __init__(self, mi, ma, inc):
        self.mini = mi
        self.maxi = ma
        self.inc = inc
        self.x = mi
        
    def get(self):
        x = self.x + self.inc
        if x > self.maxi or x < self.mini:
            self.inc = -self.inc
        else:
            self.x = x
        return self.x
    
          
        
class MiniImu(threading.Thread, LoggingObject):
    def __init__(self, filename, fake=False):
        threading.Thread.__init__(self)
        LoggingObject.__init__(self, "%s.imu.out", "wb")
        self.pitchAvg = RollingAverage(100);
        self.rollAvg = RollingAverage(100);
        self.rollTrim = self.pitchTrim = 0.0;
        
        self.filename = filename;
        self.g=self.ax=self.ay=self.az=self.pitch=self.roll=self.yaw=0
        self.rx=self.ry=self.rz=self.hx=self.hy=self.hz=0
        self.tempr=self.alt=self.press=0
        self.quit = False
        self.event = threading.Event();
        self.event.set()
        self.fakeData = False
        
        try:
         #   self.ifile = open(filename, "rb")
            self.ifile = open(filename, "r")
            self.start()
        except:
            self.ifile = False
        
            
        self.fakeG = FakeValues(.5,1.5,.05)
        self.fakeRoll = FakeValues(-65,65,1.1)
        self.fakePitch = FakeValues(-26,29,1.1)
        self.fakeYaw = FakeValues(0,360,1.5)
        
                
    def getbyte(self):
        try:
            b = self.ifile.read(1);
            self.logByte(b)
            return ord(b)
        except:
            time.sleep(0.1)
            return 0
        
    def zeroTrim(self):
        self.rollTrim = -self.rollAvg.average();
        self.pitchTrim = -self.pitchAvg.average();
        
    def read16(self):
        v = self.getbyte() * 256 + self.getbyte()
        if v > 32768:
            v = -(v - 32768)
    #    print "read16 %04d" % v
        return v

    def run(self):
        while self.quit == False:
            self.readpacket()

    def waitNow(self):
        if False and self.ifile != False:            
            self.event.wait(1.0)
            rval = self.event.isSet()
            self.event.clear()
            return rval
        
        if self.fakeData:
            self.roll = self.fakeRoll.get()
            self.yaw = self.fakeYaw.get()
            self.pitch = self.fakePitch.get()
            self.g = self.fakeG.get()
        return True
    
    def readpacket(self):
        while(True):
           try:
               l = self.ifile.readline();
               print l
               words = l.split()
               self.pitch = float(words[3]) * 180 / 3.1415
               self.roll = float(words[5]) * 180 / 3.1415
           except:
               self.pitch = self.roll = 0;

        while(True):
            b=self.getbyte()
            #if (b != 0xa5 and b != 0x25):
            #    #print "bogosu header1 %x " % b
            if (b == 0xa5 or b==0x25):
                b=self.getbyte()
                #if (b != 0x5a):
                #    print "bogus byte %x" % b
                if (b == 0x5a):
                    #time.sleep(0.05)
                    plen=self.getbyte()
                    ptyp=self.getbyte()
                    #print "plen %x " % plen
                    #print "ptyp %x " % ptyp
                    if (ptyp==0xa2):
                        self.ax=self.read16()
                        self.ay=self.read16()
                        self.az=self.read16()
                        self.rx=self.read16()
                        self.ry=self.read16()
                        self.rz=self.read16()
                        self.hx=self.read16()
                        self.hy=self.read16()
                        self.hz=self.read16()
                        self.getbyte()
                        t=self.getbyte()
                        self.g = math.sqrt(self.ax * self.ax + self.ay * self.ay + self.az * self.az)/16000/0.95
                        return
        #                if (t==0xaa):
        #                    print "got good a2 packet!"
                    if (ptyp==0xa1):
                        self.yaw = float(self.read16())/10 - 180
                        if self.yaw < 0:
                            self.yaw += 360
                        pitch = -float(self.read16())/10;
                        self.pitchAvg.add(pitch);
                        self.pitch = pitch + self.pitchTrim;
                        roll = -float(self.read16())/10;
                        self.rollAvg.add(roll);
                        self.roll = roll + self.rollTrim;
                        if self.roll > 180:
                            self.roll -= 180
                        if self.roll < -360:
                            self.roll += 360
                        self.alt=self.read16() * 3.281 / 10
                        self.tempr=self.read16()
                        self.press=self.read16()
                        self.read16()
                        self.getbyte()
                        t=self.getbyte()
                        #if (t==0xaa):
                        #    print "got good a1 packet!"
                        self.event.set()
                        self.freshData = True
                        #time.sleep(.11)
                        
          
                        return
        

            
