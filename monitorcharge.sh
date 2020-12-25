#!/bin/bash
while true; do
	minute=`date +%M`
	if [ "$lastmin" != "$minute" ]; then 
		adb shell 'dumpsys power | grep mBatteryLevel=' | sed s/mBatteryLevel=//
	fi
	lastmin=$minute
	sleep 1
done

