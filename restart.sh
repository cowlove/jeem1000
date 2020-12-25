#!/bin/sh

killall -9 python python2.7
sleep 1
cd ~/workspace/jeem1000
DISPLAY=:1.0 nohup python j.py &
exit



