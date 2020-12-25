class SerFun():
    
    def __init__(self, tty):
        self.tty = tty
        self.ifile = open(tty, "w")
        self.rpm = self.gamps = self.egt1 = self.egt2 = self.cht = self.ff = self.fp = self.amps = self.heading = 0
        self.count = 0 
    def display(self):     
        self.count += 1
	self.ifile.write("\xfe\x80%4d %3d/%3d %3d%.1f %.1f %03d %d" % 
                          (self.rpm, self.egt1, self.egt2, self.cht, self.fp, self.ff, 
                            self.heading, self.count % 10))
        self.ifile.flush()
    
