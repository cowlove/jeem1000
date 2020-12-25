import time
import os
from threading import RLock

class LoggingObject():
    def __init__(self, filename, flags = "w"):
        self.logFilename = filename;
        self.flags = flags
        self.logFile = False
        self.logStartedTime = 0
        self.logDir = "/tmp/"
        self.freshData = False
        self.fakeData = False
        self.lock = RLock()
        self.errors = 0
    
    def isFresh(self):
        rval = self.freshData or self.fakeData
        self.freshData = False
        return rval
    
    def logError(self, line):
        self.errors += 1
   
    def setLogDir(self, logD):
        self.logDir = logD;
        
    def setLog(self, active, index):
        with self.lock:
            if (active):
                try:
                    filename = (self.logDir + self.logFilename) % index
                except:
                    filename = self.logDir + self.logFilename
                self.logFile = open(filename, self.flags)
                self.logStartedTime = time.time()
            else:
                self.logFile = False        
            return 0
    
    def flush(self):
        with self.lock:
            if self.logFile != False:
                self.logFile.flush()
                os.fsync(self.logFile.fileno())
        
    def logLine(self, s):
        with self.lock:
            if (self.logFile != False):
                self.logFile.write(s)
                self.flush()
            
    def logByte(self, b):
        with self.lock:
            if (self.logFile != False):
                self.logFile.write(b)
        
    def getFileLength(self):
        with self.lock:
            return self.logFile.tell() if self.logFile != False else 0
        
    def getActiveSeconds(self):
        with self.lock:
            return time.time() - self.logStartedTime if self.logFile != False else 0


