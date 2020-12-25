#!/usr/bin/python

#import _lsprof
import sys
#import and init pygame
import pygame
import pygame.joystick
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
import os.path
import sectionalChart
from efis import RunningAverage, UdpDataLink
from threading import Thread

from miniimu import MiniImu
from ratetimer import RateTimer
from circshape import Limit, CircShape, TickSet, Arc, TextRenderCache
from colors import *
from verticaltape import VerticalTape
from pfddisplay import PfdDisplay
from tach import Tach, TachPair, TachMultiple
from annunciator import CentralAnnunciatorChannel
from hsi import HsiArc
from horizontaltape import HorizontalTape
from efis import EfisLink
from gps import LoggingObject
from efis import AdcLink
from gps import Gps
import datetime
from pygame.constants import SRCALPHA
from runningLeastSquares import RunningLeastSquares
from touchBox import *
from __builtin__ import False
from guageHistory import *
from leastSquaresVisualizer import *

window=0
class FrameRateDelay():
    def __init__(self, ms):
        self.ms = ms
        self.last = datetime.datetime.now()
        
    def wait(self):
        now = datetime.datetime.now()
        until = self.last + datetime.timedelta(microseconds=self.ms*1000)
        if until > now: 
            time.sleep((until - now).total_seconds())
        self.last = until
    

class AudioRecorder(LoggingObject):
    def __init__(self, path):
        LoggingObject.__init__(self, path)
        
    def setLog(self, active, index):
        if active:
            filename = self.logFilename % index
            #os.system("arecord -fcd -c1 | lame  -r -mm -f -v - " + filename + "&")
        else:
            os.system("killall arecord")
            
class SoftwareUpgradeButton(PushButtonBox):
    def __init__(self, window, r):
            PushButtonBox.__init__(self, window, r, ("UPGRADE",))
    
    def onChange(self, value):
        os.system("sh -c 'cd ~/workspace/jeem1000 && cvs update'")
        return PushButtonBox.onChange(self, value)        

def __main__():
    homeDir = os.getenv("HOME", "/home/jim")
    confDir = homeDir + "/adc-conf/"
    logDir = homeDir + "/log/"
    imu=MiniImu(confDir + "tty.imu")
    efis = EfisLink(confDir + "tty.efis", 0)
    gps = Gps(confDir + "tty.gps", 0)
    adc = AdcLink(confDir + "tty.adc", 0)
    udpLink = UdpDataLink(11667, 0)
    log = LoggingObject("%s.log.out", "w")
    permLog = LoggingObject("permalog.out", "a")
    permLog.setLogDir(logDir);
    permLog.setLog(True, 0)
    audioLog = AudioRecorder("%s.mp3")
    #led = BeagleboneLED(1)
    annunc = CentralAnnunciatorChannel()
    chart = sectionalChart.SectionalChart(confDir)
    
    loggerList = (udpLink, gps, efis, adc, log, audioLog, chart.adsb)
    pygame.init() 
    pygame.joystick.quit()  # Leave disconnected, so code below can initialize 
    
    #create the screen
    mode = pygame.HWSURFACE | pygame.HWACCEL
    window = pygame.display.set_mode((0,0), mode, 0) 
    
    delay = FrameRateDelay(1000/15)
    
    mapTouchHandler = TouchHandler();
    adminTouchHandler = TouchHandler();

    x = 730
    y = 95
    w = 31
    tach=TachPair(window, (x,y), w*3, (0,7500), (0,35))
    tach.title = "RPM"
    tach.format = "%.0f"
    tach.addColor(4000,5800,green)
    tach.addColor(5800,6700,yellow)
    tach.addColor(6700,7000,red)
    tach.configureAnnunciator(annunc, "R P M", 100, 100)
    tach.right.title = "MAP"
    tach.right.format = "%.1f"
    tach.right.addColor(20,32,green)
    tach.select_together = False
    
    egt=TachPair(window, (x+w*6.3,95),w*3,(0,1300), (0,1300))
    egt.title = "EGT " + u'\u00b0' + "F"
    egt.titletextpos = 270
    egt.titletextanchor = 0
    egt.textpos = 280
    egt.textanchor = 5
    egt.value = 1080
    egt.right.value = 1110
    
    for f in (egt,egt.right):
        f.addColor(900,1100,green)
        f.addColor(1100,1150,yellow)
        f.addColor(1150,1300,red)
    
    y += w*5.1
    cht=Tach(window, (x-w, y), w*2, (0,240))
    cht.title = "CHT " + u'\u00b0' + "F"
    cht.configureAnnunciator(annunc, "cylinder temp", 5)
    cht.value = 140
    cht.addColor(140,160,green)
    cht.format = "%d"

    fpres=Tach(window, (x+w*3.2, y), w*2, (0,10))
    fpres.title="Fuel PSI"
    fpres.configureAnnunciator(annunc, "fuel pressure", 1.0)
    fpres.addColor(3,7,green)
    fpres.format = "%.1f"
    fpres.value = 2.2
    
    
    fflow=Tach(window, (x+w*7.4, y), w*2, (0,10))
    fflow.title="Fuel GPH"
    fflow.addColor(3,7.5,green)
    fflow.format = "%.1f"
    fflow.value = 5.1
    fflow.configureAnnunciator(annunc, "fuel flow", 1.0)
    
    y += w*4.1
    temps = TachMultiple(3, window, (x-w, y), w*2, (0,100))
    temps.title = "Misc Temps"

	
    gmeter=Tach(False, (x-w, y), w*2, (-3,3), (20,340))
    gmeter.addColor(2,2.1,red)
    gmeter.title = "G Load"   
    gmeter.addColor(-1.1,-1,red) 
    gmeter.addColor(0,0.1,yellow) 
    gmeter.addColor(1,1.1,green) 
    gmeter.addColor(-1.1,-1,red) 
    gmeter.format = "+%.2f"
    gmeter.value = 1.0
    
    volts=Tach(window, (x+w*3.2, y), w*2, (0,15))
    volts.title="Volts"
    volts.addColor(12,14,green)
    volts.format = "%.1f"
    volts.value = 12.5

    # Only use one of amps or oat, both use the same space
    amps=TachPair(window, (x+w*7.4, y), w*2, (-20,20), (0, 20), (20,340), (180,20))
    amps.title = "BAT"    
    amps.addColor(0,5,green)
    amps.addColor(-20,-1,red)
    amps.format = "+%.1f"
    amps.value = 0
    amps.right.title = "GEN"
    amps.right.format = "%.1f"

    # Only use one of amps or oat, both use the same space
    oat=TachPair(window, (x+w*7.4, y), w*2, (0,100), (100, 0), (-10,270), (-10,270))
    oat.title = "OAT"    
    oat.format = "%.1f"
    oat.value = 0
    oat.right.title = "ALT"
    oat.right.format = "%.1f"
    
    y += w*4.5
        
    hist = GuageHistoryDisplay(window, pygame.Rect(x-w*3,y-w*2.2,w*12.2,w*3))

    trafficToggleButton = PushButtonBox(window, pygame.Rect(x+w*5.5,y-w*5.3, w*4, w*3), ("SHOW", "TRFC"))
    navZoomOutButton = PushButtonBox(window, pygame.Rect(x+w*5.5,y-w*8.4, w*4, w*3), ("ZOOM","OUT"))
    navZoomInButton = PushButtonBox(window, pygame.Rect(x+w*5.5,y-w*11.5, w*4, w*3), ("ZOOM","IN"))
    trackUpToggleButton = PushButtonBox(window, pygame.Rect(x+w*5.5,y-w*14.6, w*4, w*3), ("TRACK","UP"))
    mapInfoBoxButton = PushButtonBox(window, pygame.Rect(w*.5,w*.5, w*4, w*3), ("GS: 0", "VS: 0"))
    mapInfoBoxButton.fontSize *= w*3 / mapInfoBoxButton.rec.height # scale font down if bigger box
    guages = (volts,tach,egt,gmeter,fpres,fflow,cht,oat,temps)

    hsi=HsiArc(window, (320,450), 95)
    hsi.configureAnnunciator(annunc, "heading", 5)
    
    asi=PfdDisplay(window, (280, 200), 180)
    asi.vt1.configureAnnunciator(annunc, "air speed", 5)
    asi.vt2.configureAnnunciator(annunc, "altitude", 50, 10)
    asi.vt2.rateDisplay.configureAnnunciator(annunc, "vertical speed", 20, 10)
    
    y = 350
    timer1 = UserTimerBox(window, pygame.Rect(450,y,180,45))
    y += 50
    timer2 = EngineRunTimerBox(window, pygame.Rect(450,y,180,45), asi.vt1.history)
    timer2.title=("FLT","TIME")
    y += 50
    timer3 = EngineRunTimerBox(window, pygame.Rect(450,y,180,45), tach.history)
    y += 50
    timer4 = RpmLimitTimerBox(window, pygame.Rect(450,y,180,45), tach.history)
    markButtonBox = OneShotButton(window, pygame.Rect(450,y,180,45), ("MARK LOG",))
    zeroAttitudeButton = OneShotButton(window, pygame.Rect(250,y,180,45), ("ZERO ATT",))
  
    y = 350
    annunciateButton = AnnunciateButton(window, pygame.Rect(10, y, 180, 60), hist)
    y += 65
    recordButton = RecordButton(window, pygame.Rect(10, y, 180, 60), logDir, loggerList)
    y += 65
    mapToggleButton = DisplayModeButton(window, pygame.Rect(10, y, 180, 60))
    mapToggleButton.value = 0
                                        
    y = 20
    fakeButton = FakeValuesButton(window, pygame.Rect(10, y, 200, 95))
    y += 100
    shutdownButton = ShutdownDisplayButton(window, pygame.Rect(10, y, 200, 95))
    y += 100
    altitudeSourceButton = AltitudeSourceButton(window, pygame.Rect(10, y, 200, 95))
    y += 100
    mapSourceButton = PushButtonBox(window, pygame.Rect(10, y, 200, 95), ("CHANGE", "MAP"))
    newLogsTextBox = UploadLogsButtonBox(window, pygame.Rect(635, 500,180,45))
    newLogsTextBox.fontSize = 0.7
    softwareUpgradeButton = SoftwareUpgradeButton(window, pygame.Rect(820, 500, 180, 45))
    
    buttons = (timer1, timer2, timer3, markButtonBox, recordButton,  annunciateButton, 
               mapToggleButton)
    for g in guages + (hsi, asi.vt1, asi.vt2, asi.vt2.rateDisplay):
        hist.addGuage(g)
    for x in buttons + (hist, ):
        hist.addOtherTouchable(x)

    dispitemsPfd = guages + buttons + (hist, hsi, asi) 
    dispitemsMap = (mapToggleButton, trafficToggleButton, navZoomOutButton, navZoomInButton, trackUpToggleButton,
                    mapInfoBoxButton)
    visualizers = [LeastSquaresVisualizer(window,pygame.Rect(220,50+y*100,800,95),1) for y in range(4)]
    visualizers[0].label = "IAS"
    visualizers[0].rmsScale = 10
    visualizers[1].label = "GS" 
    visualizers[1].rmsScale = 10
    visualizers[2].label = "GSVI"
    visualizers[2].rmsScale = 0.1
    visualizers[3].label = "IVSI"
    visualizers[3].rmsScale = 1
    
    dispitemsAdmin = (fakeButton, shutdownButton, altitudeSourceButton, mapToggleButton, 
                      mapSourceButton, recordButton, markButtonBox, newLogsTextBox, 
                      softwareUpgradeButton, zeroAttitudeButton)
    for v in visualizers:
        dispitemsAdmin += (v,)

    for x in dispitemsMap:
        mapTouchHandler.add(x.get_rect(), x)
    for x in dispitemsAdmin:
        adminTouchHandler.add(x.get_rect(), x)
       
    rateTimer=RateTimer(100)
    count=0
    
    #input handling (somewhat boilerplate code):
    clickpoint=(0,0)
    longclicktimer = 0
    lastLogTime = time.time()
    lastTime = 0
    
    fakeButton.value = False
    trafficToggleButton.value = True
    glideSlopeAverager = RunningAverage(60)
        
    startTime = time.time();
    while True: 
        newSecond = int(lastTime) != int(time.time())
        newMinute = int(lastTime / 60) != int(time.time()/60)
        lastTime = time.time()
        runTime = lastTime - startTime

        # Attach/detach/reattach joystick interface to generate joystick button events 
        try:
            if os.path.exists("/dev/input/js0") and pygame.joystick.get_init() == False:
                pygame.joystick.init()
                pygame.joystick.Joystick(0).init()
                print "Joystick connected"
            if not os.path.exists("/dev/input/js0") and pygame.joystick.get_init() == True:
                pygame.joystick.quit()
                print "Joystick disconnected"
        except:
            print "Error opening/closing joystick"
            pygame.joystick.quit()

        
        #imu.readpacket()
        #draw it to the screen
        #pygame.display.update((0,0,1024,600))
        #time.sleep(0.02)
        if len(sys.argv) < 1:
            delay.wait()
        
        force = False
        w=5
        vs = 550
      
        if mapToggleButton.value == 1:
            currentTouchHandler = mapTouchHandler
        if mapToggleButton.value == 0:
            currentTouchHandler = hist
        if mapToggleButton.value == 2:
            currentTouchHandler = adminTouchHandler

        if longclicktimer > 0: # TODO - base this on time, not frame count
            longclicktimer -= 1
            if longclicktimer <= 0:
                currentTouchHandler.dispatchTouch(True, clickpoint)
                
        for event in pygame.event.get(): 
            if event.type==pygame.KEYDOWN and event.key == 113:
                annunc.quit = imu.quit = adc.quit = efis.quit = gps.quit = udpLink.quit = True
                print "EXIT"
                pygame.quit()
                time.sleep(2)
                sys.exit(0) 
            if event.type != pygame.MOUSEMOTION:
                    print event
            if event.type == pygame.MOUSEBUTTONDOWN:
                #pygame.display.toggle_fullscreen()
                force = True
                currentTouchHandler.dispatchTouch(False, event.pos)
                clickpoint = event.pos
                longclicktimer = 15
                
            if event.type == pygame.MOUSEBUTTONUP:
                longclicktimer = 0

            if event.type == pygame.KEYDOWN:
                print event

            if event.type == pygame.JOYBUTTONDOWN:
                print event
                if event.button == 1 and recordButton.value == False:  	# Down button
                    recordButton.onTouch(False, (0,0))
                if event.button == 2 and recordButton.value == True: 	# Up Button
                    recordButton.onTouch(False, (0,0))
		if event.button == 3:					# Right button
		    markButtonBox.onTouch(False, (0,0))
		if event.button == 9:					# Power button
		    mapToggleButton.onTouch(False, (0,0))
 
            if event.type == pygame.JOYHATMOTION:
                print event
        
                                
        count += 1
        if len(sys.argv) > 1 and count > int(sys.argv[1]):
            imu.quit = adc.quit = efis.quit = gps.quit = True
            pygame.quit()
            sys.exit(0) 
            return
                 
        if count == 10:
            force = True
            #fakeButton.value = False
            #recordButton.onTouch(False, (0,0))
            #pygame.display.toggle_fullscreen()
      
        if count % 60 == 0:
            force = True
            
        if (imu.waitNow() == False):
            sys.stdout.write("X")
            os.system("killall -9 i2c")
            time.sleep(1)
        #else:
        #    sys.stdout.write(".")
        sys.stdout.flush()
        
        asi.oat = adc.oat = efis.oat  # adc needs to know oat 
        

        #tach.right.value = rateTimer.rate()
        if fakeButton.changed() == True:
            chart.adsb.setFakeInput(fakeButton.value)
        
        fakeMotion = fakeButton.getFakeValues()
        if fakeMotion == 0:
            tach.value = efis.rpm
            fflow.value = efis.ff
            amps.value = efis.bamp
            amps.right.value = efis.gamp
            oat.value = asi.oat
            oat.right.value = udpLink.getValue("TEMPS.cht")
            tach.right.value = efis.map
            fpres.value = efis.fp
            asi.vt1.value = adc.ias
            if altitudeSourceButton.value == 0:
                asi.vt2.value = gps.altitude
            if altitudeSourceButton.value == 1:
                asi.vt2.value = adc.pressAlt
            if altitudeSourceButton.value == 2:
                asi.vt2.value = imu.alt
            asi.densityAlt = adc.densityAlt
            asi.tas = adc.tas
            egt.value = efis.egt1
            egt.right.value = efis.egt2
            cht.value= efis.cht 
            volts.value = efis.volts
            hsi.track = gps.course

            gps.fakeData = imu.fakeData = False
        else:
            gps.fakeData = imu.fakeData = True
            asi.tas = asi.vt1.value + 5
            hsi.track = hsi.deg
            gps.altitude = runTime * 10

        temps.value =          udpLink.getValue("temp.0215030858ff");
        temps.tachs[0].value = udpLink.getValue("temp.0315043b3fff");
        temps.tachs[1].value = udpLink.getValue("temp.0315043de1ff");
        
        if recordButton.changed() and recordButton.value:
            for v in visualizers:
                v.clear()

        if (True or recordButton.value):
            if adc.isFresh():
                visualizers[0].add(adc.ias)
            if gps.isFresh():
                visualizers[1].add(gps.speed)
                visualizers[2].add(gps.altitude * 60)
            if imu.isFresh():
                visualizers[3].add(imu.alt * 60)
                        
        hsi.deg = imu.yaw
        asi.deg = imu.roll
        asi.pitch = imu.pitch
        asi.groundSpeed = gps.speed
        asi.gpsValid = hsi.gpsValid = gps.valid()
        if not asi.gpsValid:
            asi.groundSpeed = 0
        
        if newSecond:
            vsMph = float(asi.vt2.rateDisplay.value) / 5280 * 60;
            if (asi.tas > abs(vsMph)): 
                hsMph = math.sqrt(asi.tas * asi.tas - vsMph * vsMph)
                glideSlope = vsMph / hsMph
            else:
                glideSlope = 0
            glideSlopeAverager.add(glideSlope)
            asi.slope = glideSlopeAverager.average()
                
        gmeter.value = imu.g

        if zeroAttitudeButton.check():
            imu.zeroTrim()
            
        for g in guages:
            if (fakeMotion == 0 and g.fakeMotion != 0):
                g.fakeMotion = 0
            if (fakeMotion != 0 and g.fakeMotion == 0):
                g.fakeMotion = fakeMotion

        # Log line once every second or so  
        t = time.time();
        logLinesPerSecond = 4
        if int(lastLogTime * logLinesPerSecond) != int(t * logLinesPerSecond):
            s = "t=%.2f rpm=%d ias=%.1f gs=%.1f " % (log.getActiveSeconds(), tach.value, asi.vt1.value, asi.groundSpeed)
            s += "pa=%d hd=%d trk=%d pit=%.2f roll=%.2f " % (adc.pressAlt, hsi.deg, hsi.track, asi.pitch, asi.deg)
            s += "g=%.2f map=%.2f ff=%.2f fp=%.2f " % (gmeter.value, tach.right.value, fflow.value, fpres.value)
            s += "egt1=%d egt2=%d cht=%d v=%.2f " % (egt.value, egt.right.value, cht.value, volts.value)
            s += "vs=%d epoch=%.2f gpsalt=%d " % (asi.vt2.rateDisplay.value, t, gps.altitude)
            s += "imulog=%d efislog=%d gpslog=%d adclog=%d ialt=%d mark=%d px4alt=%.1f\n" % (imu.getFileLength(), efis.getFileLength(), 
                                                                 gps.getFileLength(), adc.getFileLength(), imu.alt,
                                                                 int(markButtonBox.check()), oat.right.value)
            s += "temp1=%.1f temp2=%.1f temp3=%.1f " % (temps.value, temps.tachs[0].value, temps.tachs[1].value)
            s += "\n"
            lastLogTime = t;
            log.logLine(s)
            recordButton.redraw = True
            
            if newMinute:

                # Get android tablet battery level
                #try:
                #    androidBatt = subprocess.check_output(["sudo", "adb", "shell", "echo -n `dumpsys power | grep mBatteryLevel=`",])
                #except:
                androidBatt= "mBatteryLevel=-1"
                
                permLog.logLine("%s lat=%f lon=%f nsat=%d hdop=%.1f log=%d hbs=%.2f ftot=%d ali=%d apl=%d" % (time.strftime("%Y/%m/%d %H:%M:%S"), 
                    gps.lat, gps.lon, gps.numsat, gps.hdop, recordButton.index, efis.hobbes_minutes,
                    efis.fuel_total, chart.adsb.linesReceived, len(chart.adsb.planes))
                                + " " + androidBatt + " " + s)
                print "ERRORS ADC:%d GPS:%d EFIS:%d" % (adc.errors, gps.errors, efis.errors)
                permLog.flush()


        window.fill((0,0,0))
        pygame.draw.line(window, blue, (0,vs+w),(1024+w,vs+w), w)
        pygame.draw.line(window, blue, (1024+w,0),(1024+w,vs+w), w)

        updates = ()
        if (mapToggleButton.value == 1):
            # ugh, have to call .draw() for all the non-displayed guages so they update histories, etc
            for f in dispitemsPfd:
                f.draw(force, True)
            window.fill((0,0,0)) # then re-clear window
            
            if navZoomOutButton.value:
                navZoomOutButton.value = False
                chart.scale = min(8, chart.scale * 2)
            if navZoomInButton.value:
                navZoomInButton.value = False
                chart.scale = max(0.5, chart.scale / 2)
            chart.myAlt = asi.vt2.value - asi.vt2.value % 20
            mapInfoBoxButton.title = ("GS: %d" % asi.groundSpeed, "VS: %d" % asi.vt2.rateDisplay.value)
            if gps.lat < 1:
                #gps.lat = 48.113478
                #gps.lon = -122.135277
                gps.lat = 47.543994833333336
                gps.lon = -122.3205255
            if trackUpToggleButton.value:
                track = hsi.track
            else:
                track = 0
            updates = chart.draw(window, (gps.lat, gps.lon), track, hsi.track, showTraffic=trafficToggleButton.value)
            mapToggleButton.activeColor = (255,255,255)
            
            trafficToggleButton.blink = trafficToggleButton.value == False and chart.adsbTargetsExist()
            for b in dispitemsMap:
                b.backgroundColor = (0,0,0,80)
                b.color = (255,255,255)
                updates += b.draw(True, False)
            
        if mapToggleButton.value == 0:
            for f in dispitemsPfd:
                updates += f.draw(force, False)
            #if (count % 1 == 0):
            #    updates += asi.draw(force, False)
        
        if mapToggleButton.value == 2:
            for f in dispitemsAdmin:
                updates += f.draw(True, False)
            if mapSourceButton.value == True:
                chart.selectNextChart()
                mapSourceButton.value = False 
            mapSourceButton.title = ("MAP SRC:", chart.chart.name)
    
			
    
        if force:
            pygame.display.flip()
        else:        
            pygame.display.update(updates)

        #led.blink()
      #  if (count % 100) == 0:
      #      print "%.2f" % tach.value
        #time.sleep(0.01)
        
       # hsi.random(1)
    #    tach.move(10)
    #    asi.move(2)
    #    time.sleep(.2)
    
__main__()

