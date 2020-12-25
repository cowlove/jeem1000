from runningLeastSquares import *
from colors import *
from math import *
import sys, string

period = 20

altLs = RunningLeastSquares(2,0,period)
iasLs = RunningLeastSquares(1,0,period)


for l in sys.stdin:
	tokens = string.split(l)
	t = float(tokens[0])
	rpm = float(tokens[1])
	ias = float(tokens[2])
	galt = float(tokens[19])
	
	if rpm > 6100 or rpm < 2500:
		altLs.add(t,galt)
		iasLs.add(t,ias)
		altLs.calculate(t, 2)
		iasAvg = iasLs.calculate(t, 1)
		climb = altLs.coefficients[1] * 60 

		if  iasLs.size() >= period and iasAvg > 0 and galt > 0 and iasLs.rmsErr /  iasAvg < 0.013 and altLs.rmsErr / galt < 0.003:
			print t, ias, iasAvg, iasLs.rmsErr, galt, climb, altLs.rmsErr
		
