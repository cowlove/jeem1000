from fcntl import fcntl, F_GETFL, F_SETFL
from subprocess import Popen, PIPE
import os
import re
import time
from loggingObject import LoggingObject

class ADSBTraffic():
    def __init__(self, ident = "", lat = 0, lon = 0, alt = 0, hdg = 0, gs = 0):
        self.lat = lat
        self.id = ident
        self.lon = lon
        self.alt = alt
        self.hdg = hdg
        self.gs = gs
        self.addr = ""
        self.id = ""
        self.lastSeen = 0
        
    

class ADSBReceiver(LoggingObject):
    def __init__(self):
        LoggingObject.__init__(self,"%s.adsb.out")
        self.fd = False
        self.openInput(False)
        self.planeLat = self.planeLon = 0;
        self.planes = dict()
        self.address = ""
        self.planes[""] = ADSBTraffic()
        self.linesReceived = 0

    def setFakeInput(self, fake):
        self.openInput(fake)
        
    def openInput(self, fake):
	if (self.fd != False):
            self.fd.close()
        pipe="/tmp/dump1090.pipe"
        os.system("rm -f " + pipe)
        os.system("mknod " + pipe + " p")
        #os.system("killall sh dump1090 rtl_sdr")
        homeDir = os.getenv("HOME", "")
        if fake:
            os.system("while sleep 1; do zcat " + homeDir + "/uat.out.gz; done | grep '^-' | delaycat .02| uat2text  > " + pipe + " &")
        else:
            os.system("while sleep 2; do rtl_sdr -f 978000000 -s 2083334 -g 48 - | dump978 | uat2text; done  > " + pipe + " 2>&1 &")
	self.fd  = open(pipe, "rw")
            
                    
    def parseTraffic(self) :
        lines = 0
        while self.fd != False:
            fcntl(self.fd, F_SETFL, fcntl(self.fd, F_GETFL) | os.O_NONBLOCK)
            try:
                l = self.fd.readline()
            except:
                break
                
            self.logLine(l)
            self.linesReceived += 1
            m = re.match("CRC", l)
            if m:
                self.address = ""
                
            m = re.match(".*Address\s*:\s*([0-9a-fA-F]+)", l)
            if m:
                self.address = m.group(1)
                if not self.address in self.planes:
                    self.planes[self.address] = ADSBTraffic();
                    self.planes[self.address].addr = self.address
                self.planes[self.address].lastSeen = time.time()
                if self.planes[self.address].id == "":
                    self.planes[self.address].id = self.address 
                #print "ADS-B address ", self.address
            m = re.match("\s*Heading\s*:\s*([0-9]+)\s*$", l);
            if m:
                self.planes[self.address].hdg = int(m.group(1))

            m = re.match("\s*Track\s*:\s*([0-9]+)\s*$", l);
            if m:
                self.planes[self.address].hdg = int(m.group(1))

            m = re.match(".*Identification\s*:\s*([0-9a-zA-Z]+)", l)#s*:\s*([A-Za-z0-9]+)", l);
            if m:
                self.planes[self.address].id = m.group(1)

            m = re.match(".*Callsign\s*:\s*([0-9a-zA-Z]+)", l)#s*:\s*([A-Za-z0-9]+)", l);
            if m and m.group(1) != "unavailable":
                self.planes[self.address].id = m.group(1)

            m = re.match("\s*Altitude\s*:\s*([-+0-9]+)", l);
            if m:
                self.planes[self.address].alt = int(m.group(1))
            m = re.match("\s*Latitude\s*:\s*([-+0-9.]+)\s*$", l)
            if m:
                self.planes[self.address].lat = float(m.group(1))
            m = re.match("\s*Longitude\s*:\s*([-+0-9.]+)\s*$", l);
            if m:
                self.planes[self.address].lon = float(m.group(1))
                #print "Got plane (%s, (%f,%f), %f)" % (self.plane.addr, self.plane.lat, self.plane.lon, self.plane.alt)

            lines = lines + 1
            if lines > 60:
                break

                
    def getTraffic(self):
        self.parseTraffic()
        planes = ()
        for i, v in enumerate(self.planes):
            if (time.time() - self.planes[v].lastSeen < 20):
                planes += (self.planes[v],)
        return planes
    
