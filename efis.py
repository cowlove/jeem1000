#!/usr/bin/python

import time
import threading
import re
import string
import math
import ctypes
from loggingObject import LoggingObject
from gi.overrides import override


class RunningAverage():
	def __init__(self, len):
		self.size = len;
		self.values = []
		self.total = 0.0;
		
	def add(self, v):
		if len(self.values) == self.size:
			self.total -= self.values[0]
			self.values.pop(0)
		self.total += v
		self.values.append(v)
		
	def average(self):
		if len(self.values) > 0:
			return self.total / len(self.values)
		else:
			return 0.0
		
class EfisLinkBase(threading.Thread, LoggingObject):
	def __init__(self, logname, fakeTiming):
		threading.Thread.__init__(self)
		LoggingObject.__init__(self, logname, "w")
		self.fakeTiming = fakeTiming
		self.quit = False
		self.open()
		self.start()

	def run(self):
		while self.quit == False:
			try:
				self.readpacket()
			except:
				self.close()
				self.open()
			if self.fakeTiming > 0:
				time.sleep(self.fakeTiming)
		self.close()
			

import socket
import sys

class EfisLinkBaseUdp(EfisLinkBase):
	def __init__(self, port, logname, fakeTiming):
		self.port = port
		EfisLinkBase.__init__(self, logname, fakeTiming)

	def open(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_address = ('0.0.0.0', self.port)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(server_address)
			
	def close(self):
		print "UDP close"
		if (self.sock != False): 
			self.sock.close()
		
	def readpacket(self):
		data, address = self.sock.recvfrom(4096)
		self.parseLine(data)	
		
class EfisLinkBaseFile(EfisLinkBase):
	def __init__(self, filename, logname, fakeTiming):
		self.filename = filename;
		self.ifile = False
		EfisLinkBase.__init__(self, logname, fakeTiming)

	def open(self):
		try:
			self.ifile = open(self.filename, "rw")
			self.fakeData = False
		except:
			self.ifile = False
			self.fakeData = True
	
	def close(self):
		self.ifile = False
				
	def readpacket(self):
		#time.sleep(.07)
		if (self.ifile != False):
			try:
				l = self.ifile.readline()
				if len(l) == 0:
					self.ifile = False
				else:
					self.parseLine(l)
			except:
				self.ifile = False
				
		if self.ifile == False:
			time.sleep(1)
			self.open()
		

class UdpDataLink(EfisLinkBaseUdp):
	def __init__(self, port, fakeTiming=0.0):
		EfisLinkBaseUdp.__init__(self, port, "%s.udp.out", fakeTiming)
		self.value = 0.0
		self.tokens = ()
		self.values = {}
	
	def parseLine(self, l):
		for line in string.split(l, "\n"):
			try:
				#print "parseLine %s" % line
				self.logLine(line)

				# Parse lines in the mavproxy.py STATUS output format like:
				# 71: GPS_RAW_INT {time_usec : 0, fix_type : 1, ...} 
				# and pack away as "GPS_RAW_INT.time_usec" 
				m = re.match("([\d]*)\s*(\w+)\s*[{](.*)[}]", line)
				if m:
					prefix = m.group(2)
					for pair in string.split(m.group(3), ","):
						m = re.match("\s*([\w]+)\s*:\s*(\S+)", pair)
						if m:
							key = "%s.%s" % (prefix, m.group(1)) 
							self.values[key] = float(m.group(2))
							#print "%s = %s" % (key, self.values[key])
	
				# Parse a line like 
				# /sys/bus/w1/devices/w1_bus_master1/28-0215030858ff/w1_slave:47 01 55 00 7f ff 0c 10 51 t=20437
				# into temp.0215030858ff = 20.437
				m = re.match(".*28-(.+)/w1_slave.*t=([\d]+)", line)
				if m:
					key = "temp.%s" % (m.group(1),)
					self.values[key] = float(m.group(2)) / 1000
					#print "DS18 temp udp input %s %s\n" % (key, self.values[key])
				
			except:
				self.logerror(l)
			
	def getValue(self, key):
		if key in self.values:
			return self.values[key]
		else:
			return 0.0
			
			
		
		

	

class RfcommLink(EfisLinkBaseFile):
	def __init__(self, filename, fakeTiming=0.0):
		EfisLinkBaseFile.__init__(self, filename, "%s.rfcomm.out", fakeTiming)
		self.value = 0.0
		self.tokens = ()
		
	def parseLine(self, l):
		self.logLine(l)
		self.tokens = string.split(l)
		try:
			self.value = float(self.tokens[2])
		except:
			self.logError(l)


def TestRfcomm():
	rf = RfcommLink("/dev/rfcomm1");
	while True:
		print rf.value
		time.sleep(.1)
		
		
#TestRfcomm()

class AdcLink(EfisLinkBaseFile):
	def __init__(self, filename, fakeTiming=0.0):
		EfisLinkBaseFile.__init__(self, filename, "%s.adc.out", fakeTiming)
		self.pitotAvg = RunningAverage(5)
		self.staticAvg = RunningAverage(25)
		self.cas = self.oat = self.tas = self.ias = self.pressAlt = self.densityAlt = 0.0
		
		
	def parseLine(self, l):
		self.logLine(l)
		tokens = string.split(l)
		if (len(tokens) == 5):
			try:
				xsum = 0
				for f in tokens:
					xsum += float(f)
					
				if (xsum == 0):
					#print "Good ADC line " + l
					self.pitotAvg.add(int(tokens.pop(0)))
					self.staticAvg.add(int(tokens.pop(0)))
					
					self.ias = math.sqrt(float(math.fabs(self.pitotAvg.average() - 33860))) * .791				
					staticPressure = float(self.staticAvg.average())/52075.0*29.92/30.54*29.76 # Convoluted recalibration
					
					# wikipedia Pressure Altitude article
					pa = self.pressAlt = (1-((staticPressure/29.92)**0.190284))*145366.45

					#https://www.brisbanehotairballooning.com.au/faqs/education/113-pressure-altitude-conversion.html
					#pa = self.pressAlt = (math.pow(10, (math.log10(staticPressure/29.92)/5.2558797)) - 1
					#					) / (-6.8755856 * math.pow(10, -6)) 			
					oatC = (self.oat - 32) * 5 / 9;
					self.densityAlt = 1.24 * pa + 118.8 * oatC - 1782  # TODO- check this, results seem wrong
					self.cas = self.ias * 57.7 / 65;
					self.tas = self.cas / math.sqrt(288.15/(oatC+273.15) * (staticPressure/29.92))

					self.freshData = True
				else:
					self.logError(l)
			except:
				self.logError(l)
		else:
			self.logError(l)
			
class EfisLink(EfisLinkBaseFile):
	def __init__(self, filename, fakeTiming=0.0):
		EfisLinkBaseFile.__init__(self, filename, "%s.efis.out", fakeTiming)
		self.rpmAvg = RunningAverage(5)
		self.ffAvg = RunningAverage(10)
		self.fpAvg = RunningAverage(3)
		self.iasAvg = RunningAverage(5)
		self.gampAvg = RunningAverage(10)
		self.bampAvg = RunningAverage(10)
		self.voltAvg = RunningAverage(10)
		self.mapAvg = RunningAverage(3)
		self.oatAvg = RunningAverage(3)

		self.egt1Avg = RunningAverage(10)
		self.egt2Avg = RunningAverage(10)
		self.chtAvg = RunningAverage(10)
		self.errors = 0
		self.ias = self.bamp = self.gamp = self.volts = self.map = 0.0
		self.oat = self.rpm = self.ff = self.fp = self.egt1 = self.egt2 = self.cht = 0.0
		self.oat = self.cjt = self.humidity = self.heading = 0.0
		self.compX = self.compY = self.compZ = self.tach_minutes = self.hobbes_minutes = self.fuel_total = 0.0
		
	def parseLine(self, l):
		self.logLine(l)
		tokens = string.split(l)
		#print l
		if (len(tokens) == 11 and tokens[0] == "P"):
			tokens.pop(0)
			try:
				xsum = 0
				for f in tokens[0:-1]:
					xsum += float(f)
				xsum -= float(tokens[-1])
					
				if (xsum == 0):
					# Parse P line
					self.rpmAvg.add(float(tokens.pop(0)))
					self.egt1Avg.add(float(tokens.pop(0)))
					self.egt2Avg.add(float(tokens.pop(0)))
					self.chtAvg.add(float(tokens.pop(0)))
					self.fpAvg.add(float(tokens.pop(0)))
					self.ffAvg.add(float(tokens.pop(0)))
					self.mapAvg.add(float(tokens.pop(0)))
					self.bampAvg.add(float(tokens.pop(0)))
					self.voltAvg.add(float(tokens.pop(0)))											

					self.rpm = self.rpmAvg.average()
					self.ff = self.ffAvg.average()  / 10
					self.bamp = (self.bampAvg.average() /10)
					self.map = self.mapAvg.average() / 100
					self.fp = self.fpAvg.average() /10
					self.egt1 = self.egt1Avg.average()
					self.egt2 = self.egt2Avg.average()
					self.cht = self.chtAvg.average()
					self.volts = self.voltAvg.average() / 10

				else:
					self.logError(l)
			except:
				self.logError(l)
	
		if (len(tokens) == 11 and tokens[0] == "E"):
			tokens.pop(0)
			try:
				xsum = 0
				for f in tokens[0:-1]:
					xsum += float(f)
				xsum -= float(tokens[-1])
					
				if (True or xsum == 0):
					# Parse p shit hiere
					self.oat = (float(tokens.pop(0))) / 10
					self.cjt = (float(tokens.pop(0))) / 10
					self.humidity = (float(tokens.pop(0)))
					self.compX = (float(tokens.pop(0)))
					self.compY = (float(tokens.pop(0)))
					self.compZ = (float(tokens.pop(0)))
					self.hobbes_minutes = (float(tokens.pop(0))) / 100
					self.tach_minutes = (float(tokens.pop(0))) / 100
					self.fuel_total = (float(tokens.pop(0)))
				else:
					self.logError(l)
			except:
				self.logError(l)
		
		if (len(tokens) == 20):
				try:
					xsum = 0
					for f in tokens[0:-1]:
						xsum += float(f)
					xsum -= float(tokens[-1])
						
				 	# TODO Fix all xsum calculations to use proper ctypes int16 math
					if (True or xsum == 0):
						self.ms = int(tokens.pop(0))
						self.elapsed = int(tokens.pop(0))
						self.overflows = int(tokens.pop(0))
						self.temperature = float(tokens.pop(0))
						self.humidity = int(tokens.pop(0))
						self.oat = int(tokens.pop(0))
						self.compassX = int(tokens.pop(0))
						self.heading = int(tokens.pop(0))
						
					else:
						self.logError(l)
				except:
					self.logError(l)

			
			#.0012 / 3.785 / 2
			#print "%.2f" % self.rpm + "\t%.2f" % self.ff + "\t%.2f" % self.ias + "\t%.2f" % self.amp + "\t%.2f" % self.map + "\t%.2f" % self.fp
		
#time.sleep(1000)

