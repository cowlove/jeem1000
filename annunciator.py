import threading, thread, time, os, string

class CentralAnnunciatorChannel(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.text = False
        
        pipeIn="/tmp/speech.in.pipe"
        pipeOut="/tmp/speech.out.pipe"
        os.system("killall -9 festival")
        for p in (pipeIn, pipeOut):
            os.system("rm -f " + p)
            os.system("mknod " + p + " p")
        os.system("festival -i < %s > %s &" % (pipeIn, pipeOut))
        self.fdIn  = open(pipeIn, "w")
        self.fdOut  = open(pipeOut, "r")
        self.ready = True
        self.quit = False
        self.start()
        
        
    def isReady(self):
        return self.ready == True and self.text == False
    
    def run(self):
        while not self.quit:
            while not self.ready:
                text = self.fdOut.readline()
                if string.find(text, "Utterance") > 0: 
                    self.ready = True          
            if self.text != False:
                text = self.text
                self.text = False
                self.fdIn.write("(SayText \"%s\")\n" % text)
                self.fdIn.flush()
                self.ready = False
            else:
                time.sleep(0.01)
                    
    def addAnnunciation(self, text):
            self.text = text
