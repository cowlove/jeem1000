import pygame
from circshape import TextRenderCache
import math
from math import cos,sin,radians,tan,log,pi

import colors
import sys
import string
from adsbReceiver import *
import adsbReceiver
from __builtin__ import True

FloraLL = (47.543850, -122.320514)
StationLL = (47.473829, -122.279293)
I405LL = (47.829816, -122.262803)
FactoriaLL = (47.579961, -122.174499)
ThreeTreeLL = (47.450109, -122.382553)
LakeJoyLL = (47.695860, -121.869972)
LakeStevensLL = (48.014506, -122.066675)
TieLL = (47.4166666666667, -122.466666666667)
SilcoxIslandLL = (47.128393, -122.564771)
BumpingLakeLL = (47.177656, -121.789978)


def rotatorSize(w, h, rotPt):
    dw = max(rotPt[0], 1 - rotPt[0]) * w
    dh = max(rotPt[1], 1 - rotPt[1]) * h
    return int(math.sqrt(dw*dw + dh*dh) * 2)
 
def drawAirplaneShape(sfc, rsize, col, wid):
    x = sfc.get_rect().width / 2
    y = sfc.get_rect().height / 2
    pygame.draw.polygon(sfc, col,((x,y+rsize/4),
                                  (x+rsize/4,y+rsize/2),
                                  (x,y-rsize/2),
                                  (x-rsize/4,y+rsize/2)),wid)

txtCache = TextRenderCache(colors.black)

def blitByCenter(s1, s2, xy):
    s1.blit(s2, (xy[0] - s2.get_rect().width/2, xy[1] - s2.get_rect().height/2))
        
def blurSurf(surface, amt):

    if False:
        if amt < 1.0:
            raise ValueError("Arg 'amt' must be greater than 1.0, passed in value is %s"%amt)
        scale = 1.0/float(amt)
        surf_size = surface.get_size()
        scale_size = (int(surf_size[0]*scale), int(surf_size[1]*scale))
        surface = pygame.transform.smoothscale(surface, scale_size)
        surface = pygame.transform.smoothscale(surface, surf_size)
        
    if False:
        shadSize = 3
        pa1 = pygame.PixelArray(surface)
        rval = surface.copy()
        pa2 = pygame.PixelArray(rval)
        w = surface.get_rect().width
        h = surface.get_rect().height
        for x in xrange(0,w):
            for y in xrange(0,h):
                pix = pygame.Color(pa1[x,y]);
                if pix.a > 0:
                    for x1 in xrange(x - shadSize, x + shadSize):
                        for y1 in xrange(y - shadSize, y + shadSize):
                            if x1 >= 0 and x1 < w  and y1 >= 0 and y1 < h:
                                p2 = pygame.Color(pa2[x1,y1])
                                p2.a = max(p2.a, pix.a)
                                pa2[x1,y1] = p2
        surface = rval
    return surface

    
def drawAirplane(sfc, px, col, screenAngle = 0, text1 = False, text2 = False, dimSurrounding = False):
    rsize = 45
    arrow = pygame.Surface((rsize*3,rsize*3), pygame.SRCALPHA)
    if dimSurrounding != False:
        pygame.draw.circle(arrow,(0,0,0,dimSurrounding),
                           arrow.get_rect().center,arrow.get_rect().width / 2)
    drawAirplaneShape(arrow, rsize, col, 0)
    drawAirplaneShape(arrow, rsize, colors.black, 4)
    arrow = pygame.transform.rotate(arrow, -screenAngle)    
    if text1 != False:
        blitByCenter(arrow, txtCache.text(text1, rsize, col), 
                     (arrow.get_rect().width / 2, arrow.get_rect().height / 2 - rsize*.8))
    if text2 != False:
        blitByCenter(arrow, txtCache.text(text2, rsize, col), 
                     (arrow.get_rect().width / 2,  arrow.get_rect().height / 2 + rsize*.8))
    
    
    #blur = blurSurf(arrow,5)
    #blur.blit(arrow, (0,0))
    blitByCenter(sfc, arrow, px)
    
    
class TiePoint:
	def __init__(self, lat, lon, x, y):
		self.lat = lat;
		self.lon = lon;
		self.x = x;
		self.y = y;

class ChartInfo:
    def __init__(self, centerLL, windowSize, fileName, pixelScale, tiePointMeters, tiePtLL, name):
        self.centerLL = centerLL
        self.rotang = 0
        self.scale = 1
        self.centerPx = (0,0)
        self.scaledWindowSize = windowSize
        self.earthRadius = 6371000
        self.tiePoints = ()
        self.name = name
        self.sectSfc = pygame.image.load(fileName)
        self.pixelScale = pixelScale
        self.tiePointMeters=tiePointMeters
        self.tiePtLL=tiePtLL
        self.stdParallels = (45,33)
        self.setTileCenter(centerLL, 1, 0)

    def chartToScreenPixel(self, pix, offset):  # translate from pixel of large chart to pixel in 
        # rotated/centered/scaled tile
        x = (pix[0] - self.centerPx[0]) / self.scale;
        y = (pix[1] - self.centerPx[1]) / self.scale;
        rr = math.radians(-self.rotang)
        
        x1 = math.cos(rr) * x + math.sin(rr) * y + offset[0]
        y1 = math.cos(rr) * y - math.sin(rr) * x + offset[1];
        return (x1, y1)
    
    def setTileCenter(self, centerLL, scale, rot):
        self.rotang = rot
        if centerLL == self.centerLL and scale == self.scale:
            return
        
        ws = self.scaledWindowSize * scale
        self.scale = scale
        self.centerLL = centerLL;
        self.centerPx = self.latLng2ChartPixel(centerLL)
        #self.checkPrefetch(self.centerPx, ws); 
        self.secWin = pygame.Surface((ws, ws))
        self.secWin.blit(self.sectSfc, (0,0), (self.centerPx[0] - ws / 2, 
                                          self.centerPx[1] - ws / 2,
                                          ws, ws))
        self.secWin = pygame.transform.scale(self.secWin, ((int(ws / self.scale),
                                                       int(ws / self.scale))))
        
    def getChartSurface(self, ll):
        rotSec = pygame.transform.rotate(self.secWin, -self.rotang)
        return rotSec
    
    def latLng2ChartPixel(self, locLL):
		if len(self.tiePoints) > 1:
			return self.latLng2ChartPixelMPT(locLL)
		else:
			return self.latLng2ChartPixelLambert(locLL)

    def rotate(self, rot):
        self.rotang = rot
        
    def addTiePoint(self, lat, lon, x, y):
		self.tiePoints = self.tiePoints + (TiePoint(lat, lon, x, y),)	
		
    def latLng2ChartPixelMPT(self, locLL): 
        count = 0 
        sumx = 0
        sumy = 0
        tps = self.tiePoints
        for tp1 in self.tiePoints:
            for tp2 in self.tiePoints:
                if tp1<>tp2:
                    y = tp1.y + (tp2.y - tp1.y) * (locLL[0] - tp1.lat) / (tp2.lat - tp1.lat)
                    x = tp1.x + (tp2.x - tp1.x) * (locLL[1] - tp1.lon)/ (tp2.lon - tp1.lon)
                    sumx += x
                    sumy += y
                    count += 1
					
        if count > 0:
            return (sumx/count, sumy/count) 
        else:
            return (0,0)
            
    def latLng2ChartPixelLambert(self, locLL):  # Get pixel offset into large chart object

        # calculate effective earth radius at given lat
        eRadius = 6378137.00 # equatorial and polar radius of WGS84 ellipsoid 
        pRadius = 6356752.31
        lat = radians(locLL[0])
        radius = math.sqrt(
                           ((eRadius**2*cos(lat))**2 + (pRadius**2*sin(lat))**2) / 
                           ((eRadius*cos(lat))**2 + (pRadius*sin(lat))**2))

        # Trig for lambert projection from wikipedia article on lambert projection
        stdParallel0 = radians(self.stdParallels[0])
        stdParallel1 = radians(self.stdParallels[1])
        n = (log(cos(stdParallel0)*1/cos(stdParallel1)) / 
             log(tan(pi/4+stdParallel1/2)*1/tan(pi/4+stdParallel0/2)))
        F = (cos(stdParallel0)*tan(pi/4+stdParallel0/2) ** n) / n
        rho0 = F * (1/tan(pi/4 + radians(self.tiePtLL[0]/2)))**n
        rho  = F * (1/tan(pi/4 + radians(locLL[0]/2)))**n
        dx = rho * sin(n*radians(locLL[1] - self.tiePtLL[1])) * radius
        dy = (rho0 - rho * cos(n*radians(locLL[1] - self.tiePtLL[1]))) * radius
                
        # Old rectilinear projection 
        #dy = math.sin(math.radians(locLL[0] - self.tiePtLL[0])) * self.earthRadius
        #dx = (math.sin(math.radians(locLL[1] - self.tiePtLL[1])) * 
        #	  math.cos(math.radians((locLL[0]+self.tiePtLL[0])/2)) * self.earthRadius) 
        
        locPix = ((self.tiePointMeters[0] + dx)/self.pixelScale[0], 
        		  (self.tiePointMeters[1] - dy)/self.pixelScale[1])
        return locPix

    def chartContains(self, locLL):
        chartPixel = self.latLng2ChartPixel(locLL)
        return self.sectSfc.get_rect().collidepoint(chartPixel)
		
    def latLng2ScreenPixel(self, locLL, offset):  # distance from center
        return self.chartToScreenPixel(self.latLng2ChartPixel(locLL), offset)
          
class SectionalChart():
    def __init__(self, chartDir):
        self.selfPos=(0.50,0.70) # self-center position on display screen 
        self.locLL = FloraLL
        self.rotang = 1
        self.w = 1024
        self.h = 550
        self.scale = 1
        self.myAlt= 0
        self.trackHistory = []
        self.rotSec = False
        self.showTrack = self.showTrackHistory = True
        self.adsb = adsbReceiver.ADSBReceiver()
        self.secSize = rotatorSize(self.w,self.h,self.selfPos);
        self.charts = 0
        vtf = ChartInfo(self.locLL, self.secSize, chartDir + "/vtf.jpg",
			(0,0),(0,0),(0,0), "VTF")
        vtf.addTiePoint(48.971658, -123.083681, 2826,6064) #pt robert litehouse
        vtf.addTiePoint(49.419884, -123.316009, 1280,1360) #N pt bowen island
        vtf.addTiePoint(49.159233, -122.985315, 3528,4100) #W pt annasis isl
		
        tac = ChartInfo(self.locLL, self.secSize, chartDir + "/TAC.tif",
			(21.1661265072176, 21.1656525230806), 
			(90281.1865478541, 83969.9977572564), 
			(47.4166666666667, -122.466666666667), "TAC")
        sec =                ChartInfo(self.locLL, self.secSize, chartDir + "/SEC_crop.tif", 
				(42.334884781508684,42.335597515618694), 
				(409375.329186913440935,261032.079643933713669), 
				(46.75, -121), "SEC")
        
        sec.stdParallels = (46.6666667,41.333333)
        self.charts = (tac,sec,vtf)
        self.chart = self.charts[1]
        self.setCenter((0,0), 0)
        
    def setCenter(self, ll, rotang):
        self.locLL = ll
        self.chart.setTileCenter(ll, self.scale, rotang)
       
    def selectNextChart(self):
        self.chart = self.charts[(self.charts.index(self.chart) + 1) % len(self.charts)]
         
    def draw(self, window, centerLl, rotang, hdg, showTraffic = True):
        rotang = -rotang
        chart = self.chart
        selfPos = self.selfPos;
        w = self.w
        h = self.h
        centerOffset = (w*selfPos[0], h*selfPos[1])
        self.locLL = centerLl
	
		# Not on the current chart?  Try to find one we're on
        if not chart.chartContains(self.locLL):
            for c in self.charts:
                if c.chartContains(self.locLL):
                    chart = c
                    break
			        
	    # Invalidate the rotated sectional if things have changed
        if centerLl != chart.centerLL or rotang != chart.rotang or self.scale != self.chart.scale:
            self.rotSec = False
            
        chart.setTileCenter(centerLl, self.scale, rotang)
        if self.rotSec == False:
            chart.rotate(rotang)
            self.rotSec = chart.getChartSurface(self.locLL)

        view = pygame.Rect((self.rotSec.get_rect().center[0]-w*selfPos[0], 
                                   self.rotSec.get_rect().center[1]-h*selfPos[1],w,h))
        #view.center = chart.latLng2ScreenPixel(self.locLL, (0,0))
        window.blit(self.rotSec, (0,0), view)
          
        lx = h*math.sin(math.radians(rotang+hdg))
        ly = -h*math.cos(math.radians(rotang+hdg))
        
        if self.showTrack:
		    pygame.draw.line(window, colors.magenta, (centerOffset[0],h*selfPos[1]), (lx+centerOffset[0],ly+h*selfPos[1]), 5)   
        
        if self.showTrackHistory:
            last = self.locLL;
            for p in self.trackHistory:
				pygame.draw.line(window, colors.magenta, chart.latLng2ScreenPixel(last, centerOffset),
					chart.latLng2ScreenPixel(p, centerOffset),5)
				last = p
            if (len(self.trackHistory) == 0 or abs(self.locLL[0] - self.trackHistory[0][0]) + abs(self.locLL[1] - self.trackHistory[0][1]) > 0.01):
				self.trackHistory = [self.locLL] + self.trackHistory[:500]	
		
        drawAirplane(window, chart.latLng2ScreenPixel(self.locLL, centerOffset), 
                    colors.magenta, rotang+hdg, "", "%d'" %self.myAlt)

        if showTraffic:
            for t in self.adsb.getTraffic():
                drawAirplane(window, chart.latLng2ScreenPixel((t.lat, t.lon), centerOffset), 
                             colors.cyan, rotang + t.hdg, t.id, "%d'" % t.alt, 80)

        return (pygame.Rect(0,0,w,h),)       
    
    def adsbTargetsExist(self):
        return True
        
        
if __name__ == '__main__':
    print "main"
    pygame.init() 
    if True:
        chart = SectionalChart("/home/jim/adc-conf/")
        chart.scale = 1
        chart.chart = chart.charts[0]  # vtf chart
        chart.showTrack = False
        window = pygame.Surface((chart.w,chart.h))
    	f = open("/home/jim/tmp/latlng.txt", "r")
    	lastline = False
    	values = [None] * 5
    	count = 0;
    	while True:
	        print "%d" % count
    		l = f.readline()
    		if lastline == False:
    			lastline = l
    		tokens = string.split(l)
    		ltokens = string.split(lastline)
    		if float(tokens[3]) - float(ltokens[3]) < 120:
    			if abs(float(tokens[2]) - float(ltokens[2])) > 180:
    				if (float(tokens[2]) < 180):
    					tokens[2] = float(tokens[2]) + 360
    				else:
    					ltokens[2] = float(ltokens[2]) + 360
    					
    			smooth = 5 # interpolate n extra frames 
    			for frame in xrange(0, smooth):
    				for i in xrange(0, 5):
    					values[i] = (float(tokens[i]) - float(ltokens[i])) / smooth * (frame) + float(ltokens[i])
    				chart.myAlt = values[4] 
    				chart.draw(window, (values[0], values[1]), 0, values[2], False)
    				pygame.image.save(window, "/home/jim/tmp/window%06d.jpg" % count)
    				count += 1
    		lastline = l

