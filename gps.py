#!/usr/bin/python

import time
import threading
import re
import string
import os
import operator
from loggingObject import LoggingObject
from leastSquaresVisualizer import *

FloraLL = ("4732.63369N", "12219.23753W")

class Gps(threading.Thread, LoggingObject):
	def __init__(self, filename, fakeTiming=0.0):
		threading.Thread.__init__(self)
		LoggingObject.__init__(self, "%s.gps.out", "w")
		self.filename = filename;
		self.quit = False
		self.validToken = self.numsat = self.altitude = 0;
		self.time = self.course = self.date = self.speed = 0
		self.lat = self.lon = self.hdop = 0.0
		self.errors = 0
		self.fakeTiming = fakeTiming
		self.validTime = 0
		self.freshData = self.setSystemTime = False
		self.fakeData = False
		
		try:
			self.ifile = open(filename, "rw")
			self.fakeData = False
			self.start()
		except:
			self.fakeData = True

	def isFresh(self):
		rval = self.freshData
		self.freshData = False
		return rval
	
	def run(self):
		while self.quit == False:
			self.readpacket()
			if self.fakeTiming > 0:
				time.sleep(self.fakeTiming)

	def valid(self):		
		if self.fakeData:
			if self.validTime < time.time() - 4 or abs(self.lat) < 1 or abs(self.lon) < 1:
				self.lat = self.parseLatLong(FloraLL[0])
				self.lon = self.parseLatLong(FloraLL[1])
				self.course = 130
			self.speed = 72.3
			self.altitude = 2600
			self.validTime = time.time()
			self.lat = self.lat + 0.0001 * math.sin(math.radians(self.course));
			self.lon = self.lon + 0.0001 * math.cos(math.radians(self.course));
			self.course = (self.course + .1) % 360
			return True
		else:
			valid = self.validToken > 0 and self.validTime > time.time() - 4 
			if not valid:
				self.numsat = self.hdop = 0
			return valid

	def readpacket(self):
		self.parseLine(self.ifile.readline())
	
	def checksum(self, sentence):
		try:
			sentence = sentence.strip('\n')
			sentence = sentence.strip('\r')
			nmeadata,cksum = sentence.split('*')
			calc_cksum = reduce(operator.xor, (ord(s) for s in nmeadata[1:]), 0)
			return nmeadata,int(cksum,16),calc_cksum
		except:
			return "",0,1

	def parseLatLong(self, s):
		m = re.match("([0-9]+)([0-9][0-9])(.[0-9]+)([NSEW])", s)
		rval = 0;
		if m:
			m1 = m.group(1)
			m2 = m.group(2)
			m3 = m.group(3)
			m4 = m.group(4)
			rval = float(m.group(1)) + float(m.group(2) + m.group(3))/60 
			if m.group(4) == "S" or m.group(4) == "W":
				rval = -rval
		return rval
	
	
	def parseLine(self, l):
		if len(l) == 0:
			time.sleep(0.1)
		nmea,cksum1,cksum2 = self.checksum(l)
		if cksum1 != cksum2:
			self.logError(l)
			return
			
		tokens = string.split(l, ",")
		#print l
		self.logLine(l)
		if re.match("^\$GPGGA", l):
			if (len(tokens) > 9):
				try:
					self.validToken = int(tokens[6])
					self.numsat = int(tokens[7])
					self.hdop = float(tokens[8])
					self.altitude = float(tokens[9]) * 3.281
					self.validTime = time.time()
					self.freshData = True
					#if (self.validToken > 0):
					#	os.system("sudo bash -c 'echo 1 > " + self.led + "/shot'");

				except:
					self.logError(l)
	
		if re.match("^\$GPVTG", l):
			if (len(tokens) > 5):
				try:
					self.course = float(tokens[1])
				except:
					self.logError(l)

				try:
					self.speed = float(tokens[5]) * 1.151
				except:
					self.logError(l)

		if re.match("^\$GPRMC", l):
			if (len(tokens) > 9):
				try:
					self.time = tokens[1]
					self.lat = self.parseLatLong(tokens[3] + tokens[4])
					self.lon = self.parseLatLong(tokens[5]  + tokens[6])
					# TMP HACK
					if abs(self.lat) < 1 or abs(self.lon) < 1:
						self.lat = self.parseLatLong(FloraLL[0])
						self.lon = self.parseLatLong(FloraLL[1])
						
					self.date = tokens[9]
					self.validTime = time.time()
					d = self.date
					t = self.time
					#print "%d %d" % (len(d), len(t))
					if (self.setSystemTime != True and len(d) == 6 and len(t) == 9):
						 utcSpec = d[2:4] + d[0:2] + t[0:4] + d[4:6] + "." + t[4:6]
						 print  "set time to " + utcSpec
						 os.system("sudo date -u " + utcSpec);
						 self.setSystemTime = True
						
					self.speed = float(tokens[7]) * 1.151
					self.course = float(tokens[8])   # TODO: This is magnetic, use VTG sentence instead

				except:
					self.logError(l)

				
				#print "%.2f" % self.speed + "\t%.2f" % self.course + "\t%.2f" % self.altitude + "\t" + self.lat + "/" + self.lon + "\t%d" % self.valid


#gps = Gps("/home/jim/gps.in")
#time.sleep(1000)
