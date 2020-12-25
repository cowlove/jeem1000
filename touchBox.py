import time
import pygame
import sys
#import and init pygame
import pygame
import os
import subprocess
import random
import string
import time
import math
import time
import thread
import colors
import re 
import os
import sectionalChart
from efis import RunningAverage
from threading import Thread

from miniimu import MiniImu
from ratetimer import RateTimer
from circshape import Limit, CircShape, TickSet, Arc, TextRenderCache
from colors import *
from verticaltape import VerticalTape
from pfddisplay import PfdDisplay
from tach import Tach, TachPair 
from annunciator import CentralAnnunciatorChannel
from hsi import HsiArc
from horizontaltape import HorizontalTape
from efis import EfisLink
from gps import LoggingObject
from efis import AdcLink
#from gps import Gps
import datetime
from pygame.constants import SRCALPHA
from runningLeastSquares import RunningLeastSquares
from touchableObject import *
from __builtin__ import False

class TouchArea():
    def __init__(self, rec, action):
        self.rec = rec
        self.action = action
                
class TouchHandler():
    def __init__(self):
        self.list = ()
        
    def add(self, rectangle, action):
        self.list += (TouchArea(rectangle, action),)
        
    def dispatchTouch(self, isLong, point):
        for f in self.list:
            if f.rec.collidepoint(point): 
                f.action.onTouch(isLong, point)

class TouchableObject():
    def onTouch(self, isLong, point):
        return 0
            
      
class Box(TouchableObject):
    def __init__(self, window, r):
        self.w = window
        self.rec = r
        self.thickness = 3
        self.backgroundColor = False
        self.borderColor = white # (50,50,50)
        
    def draw(self, force, noDraw):
        if noDraw:
            return ()
        if force:
            if self.backgroundColor:
                bg = pygame.Surface((self.rec.width, self.rec.height), SRCALPHA)
                bg.fill(self.backgroundColor)
                self.w.blit(bg, self.rec)
            pygame.draw.rect(self.w, self.borderColor, self.rec, self.thickness)
            return (self.rec,)
        else:
            return ()

    def get_rect(self):
        return self.rec


class TextBox(Box):
    def __init__(self, window, r, title=()):
        Box.__init__(self, window, r)
        self.textCache = TextRenderCache(white)
        self.title = title
        self.fontSize = 0.5
        self.color = (155,155,155)
        self.blink = False
        self.redraw = False

    def draw(self, force, noDraw, color=False):
        if noDraw:
            return ()
        if self.redraw:
            self.redraw = False
            force = True
        
        force = True
        if self.blink and (datetime.datetime.now().time().microsecond / 500000) % 2 == 0:
            color = black
        if color == False:
            color = self.color
        rval = Box.draw(self, force, False)
        for t in self.title:
            fs = self.rec.height * self.fontSize
            txt = self.textCache.text(t, fs, color);
            re = txt.get_rect()
            re.top = self.rec.top + self.rec.height * .05 + self.title.index(t) * re.height;
            re.left = self.rec.left + self.rec.width * .05;
            self.w.blit(txt, re)
        return rval    

class PushButtonBox(TextBox):
    def __init__(self, window, r, title=()):
        TextBox.__init__(self, window, r, title)
        self.activeColor = red
        self.value = False
        self.lastValue = False
        self.ignoreTouch = False
        
    def draw(self, force, noDraw):    
        if self.value:
            color = self.activeColor
        else:
            color = self.color            
        return TextBox.draw(self, force, noDraw, color)
            
    def changed(self):
        rval = self.value != self.lastValue
        self.lastValue = self.value
        return rval
 
    def onChange(self, value):
        return 0
        
    def setValue(self, value):
        changed = self.value != value
        self.value = value
        if changed:
            self.onChange(value)
            
    def onTouch(self, isLong, point):
        if not self.ignoreTouch:
            self.value = not self.value
            self.onChange(self.value)

class UploadLogsButtonBox(PushButtonBox):
    def __init__(self, window, r):
        PushButtonBox.__init__(self, window, r)
        
    def updateLogCount(self):
        try: 
            newLogs = subprocess.check_output(['sh', '-c', 'find ~/log/ -newer ~/log/lastupload | wc -l'])
            newLogs = int(newLogs)
        except:
            newLogs = 0
        self.title=("%d NEW FILES" % newLogs,)
        self.value = newLogs > 1
        self.draw(True, False)
        
    def draw(self, force, noDraw):    
        return PushButtonBox.draw(self, True, noDraw)
        
    def onTouch(self, isLong, point):
        self.updateLogCount()
        if True:
            try:
                subprocess.check_output(['sh', '-c', '~/workspace/jeem1000/try_upload_logs.sh'])
            except:
                False
        self.updateLogCount()
                
class PushButtonSequenceBox(PushButtonBox):
    def __init__(self, window, r, titles=(("TITLE",))):
        PushButtonBox.__init__(self, window, r, ())
        self.titles = titles
        self.title = titles[0]
        self.value = 0
        
    def onTouch(self, isLong, point):
        if isLong:
            self.value = 0
        else:
            self.value = (self.value + 1) % len(self.titles)
            self.title = self.titles[self.value]
    
    
class RecordButton(PushButtonBox):
    def __init__(self, window, r, logDir, loggableList):
        PushButtonBox.__init__(self, window, r)
        self.loggableList = loggableList
        self.value = True
        self.onTouch(False, "")
        self.logDir = logDir
        for l in self.loggableList:
            l.setLogDir(logDir)
	self.readNextFileNo()

    def draw(self, force, noDraw):
        if noDraw:
            return ()
        if self.value == True:
            force = True
        if force:
            if (self.value):
                self.fontSize = 1.0
                t = time.time() - self.loggableList[0].logStartedTime
                if math.floor(t)%2 == 0:
                    if int(t)%60 == 0:
                        self.backgroundColor = white
                        self.activeColor = red
                    else:
                        self.backgroundColor = red
                        self.activeColor = white
                    self.title = ("TIME %d" % t, )
                else:
                    self.backgroundColor = black
                    self.activeColor = red
                    self.title = ("FILE %d" % self.index, )
            else:
                self.fontSize = 0.5
                self.backgroundColor = black
                self.activeColor = red
                self.title = ("RECORD", "FILE %d" % (self.index))
        return PushButtonBox.draw(self, force, False)
    
    def readNextFileNo(self):
        try:
            f = open(self.logDir + "/nextlogfile", "r")
            nextfile= int(f.readline())
        except:
            nextfile = 1
        self.index = nextfile
            

    def onTouch(self, isLong, point):
        self.value = not self.value
	self.readNextFileNo();
        if (self.value):
            os.system(("echo %d > " + self.logDir + "/nextlogfile") % (self.index + 1))
        else:
            os.system("sync")
        for l in self.loggableList:
            l.setLog(self.value, "%d" % self.index)
        
    
class FakeValuesButton(PushButtonBox):
    def __init__(self, window, r):
        PushButtonBox.__init__(self, window, r)
        self.title = ("DEMO", "VALUES",)
        self.lastValue = False
        
    def getFakeValues(self):
        if self.value == True:
            return 0.1
        else:
            return 0.0
        
    
        

class OneShotButton(PushButtonBox):
    def __init__(self, window, r, title):
        PushButtonBox.__init__(self, window, r)
        self.title = title
        self.lastPressTime = datetime.datetime.now()
        
    def onTouch(self, isLong, point):        
        PushButtonBox.onTouch(self, isLong, point)
        self.lastPressTime = datetime.datetime.now()

    def check(self):
        rval = self.value
        self.value = False
        return rval
    
    def draw(self, force, noDraw):
        if ((datetime.datetime.now() - self.lastPressTime).total_seconds() > 5):
            self.backgroundColor = black
        else:
            self.backgroundColor = red
            
        return PushButtonBox.draw(self, force, noDraw)
    
class AnnunciateButton(PushButtonBox):
    def __init__(self, window, r, annunc):
        PushButtonBox.__init__(self, window, r)
        self.title = ("ANNUNCIATE",)
        self.annunciator = annunc
        
    def onTouch(self, isLong, point):
        PushButtonBox.onTouch(self, isLong, point)
        self.annunciator.setAnnunciatorMode(self.value)

    def draw(self, force, noDraw):
        self.blink = (self.value == True and self.annunciator.isAnnunciatorSelected() == False)
        return PushButtonBox.draw(self, force, noDraw)

class MapToggleButton(PushButtonBox):
    def __init__(self, window, r):
        PushButtonBox.__init__(self, window, r)
        self.title = ("SHOW","NAV")
        self.activeColor = cyan
        self.backgroundColor = (0,0,0,100)
        
    def onTouch(self, isLong, point):        
        PushButtonBox.onTouch(self, isLong, point)
            
    def draw(self, force, noDraw):
        if self.value:
            self.title = ("SHOW","PFD")
        else:
            self.title = ("SHOW","NAV")
        return PushButtonBox.draw(self, force, noDraw)
        
class DisplayModeButton(PushButtonSequenceBox):
    def __init__(self, window, r):
        PushButtonSequenceBox.__init__(self, window, r, (("PAGE",),("PAGE",), ("PAGE",)))

class AltitudeSourceButton(PushButtonSequenceBox):
    def __init__(self, window, r):
        PushButtonSequenceBox.__init__(self, window, r, (("GPS", "ALTITUDE"), ("STATIC", "ALTITUDE"), ("MINIIMU", "ALTITUDE")))
        
class ShutdownDisplayButton(PushButtonBox):
    def __init__(self, window, r):
        PushButtonBox.__init__(self, window, r)
        #self.title = ("SHUTDOWN", "DISPLAY",)
        self.countdown = 0
    def onTouch(self, isLong, point):        
        if self.countdown == 0:
            self.value = True 
            self.countdown = 100
        else:
            os.system("touch /tmp/pausedisplay")
            self.countdown = 0
            self.value = False
        
    def draw(self, force, noDraw):
        if self.countdown > 0:
            self.countdown -= 1
            self.title = ("PRESS AGAIN", "IN %d" % self.countdown)
        else:
            self.title = ("SHUTDOWN", "DISPLAY",)
            self.value = False
        return PushButtonBox.draw(self, force, noDraw)
    
class TimerBox(Box):
    def __init__(self, window, r, title=()):
        Box.__init__(self, window, r)
        self.textCache = TextRenderCache(white)
        self.title = title
        self.format = "%d:%02d:%02d"
        self.seconds = 0
        self.color = (155,155,155)
        self.lastTime = 0

    def start(self):
        self.lastTime = math.floor(time.time())
        
    def tick(self):
        if (math.floor(time.time()) != self.lastTime):
            self.seconds += 1
            self.lastTime = math.floor(time.time())
        
    def draw(self, force, noDraw):
        if noDraw:
            return ()
        fs = self.rec.height * 1.1
        h = self.seconds / 60 / 60
        m = ( self.seconds / 60 ) % 60
        s = self.seconds % 60
                
        txt = self.textCache.text(self.format % (h, m, s), fs, self.color);
        re = txt.get_rect()
        re.top = self.rec.top + self.rec.height * .01;
        re.left = self.rec.left + self.rec.width * .35;
        self.w.blit(txt, re)

        y = self.rec.top + self.rec.height * .05;
        
        for t in self.title:
            fs = self.rec.height * .5
            txt = self.textCache.text(t, fs, self.color);
            re = txt.get_rect()
            re.top = self.rec.top + self.rec.height * .05 + self.title.index(t) * re.height;
            re.left = self.rec.left + self.rec.width * .05;
            self.w.blit(txt, re)

        force = True
        return Box.draw(self, force, False)

    def onTouch(self, isLong, point):
        self.seconds += 1
        if (isLong):
            self.seconds = 0


class UserTimerBox(TimerBox):
    def __init__(self, window, r):
        TimerBox.__init__(self, window,r,("MISC","TIMER"))
        self.running = True
        
    def draw(self, force, noDraw):
        if (self.running):
            self.tick()
            force = True
            self.color = white
        else:
            self.color = (155,155,155)
            
        return TimerBox.draw(self, force, noDraw)
   
    def onTouch(self, isLong, point):
        if (isLong):
            self.seconds = 0
            self.running = False
        else:
            self.running = not self.running
            
        if (self.running):
            self.start()
            
            
class EngineRunTimerBox(TimerBox):
    def __init__(self, window, r, hist):
        TimerBox.__init__(self, window,r,("ENG","RUN"))
        self.hist = hist

    def draw(self, force, noDraw):
        #if len(self.hist.data) > 0 and self.hist.data[0] > self.hist.range[0] * .10 and self.hist.data[0] > 20:
        if len(self.hist.data) > 0 and self.hist.data[0] > 20:
            self.tick()
            force = True
            self.color = white
        else:
            self.color = (155,155,155)
        
        return TimerBox.draw(self, force, noDraw)

class RpmLimitTimerBox(TimerBox):
    def __init__(self, window, r, hist):
        TimerBox.__init__(self, window,r,("ENG","LIMIT"))
        self.hist = hist
        self.limits = ((5800,300), (6700,60))
        
    def draw(self, force, noDraw):
        secs = 0
        limit = False
        
        if len(self.hist.data) > 0:
            for l in self.limits:
                if self.hist.data[0] >= l[0]:
                    limit = l
         
        seen = 0
        if limit != False:
            for d in self.hist.data:
                if d > limit[0]:
                    secs += self.hist.histIntervalSeconds
                seen += 1   
                if seen > 600:
                    break
                
                self.seconds = l[1] - secs
                if self.seconds > 0:
                    self.color = white
                else:
                    self.color = red
                    self.seconds = -self.seconds
        else:
            self.seconds = 0
            self.color = (155,155,155)
            
        force = True
        return TimerBox.draw(self, force, noDraw)
                
        

   
