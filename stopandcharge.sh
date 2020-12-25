#!/bin/bash
REMOTEBIN=/data/tmp/


sudo killall x-terminal-emulator
sudo adb shell am force-stop android.androidVNC
while true; do
	# force kindle to sleep 
	minute=`date +%M`
	if [ "$lastmin" != "$minute" ]; then 
		adb shell 'dumpsys power | grep mBatteryLevel=' | sed s/mBatteryLevel=//
	fi
	lastmin=$minute
	adb shell 'dumpsys power | grep mWakefulness=Awake && input keyevent KEYCODE_POWER'	
        adb shell  $REMOTEBIN/powerwatchdog.sh
	sleep 6
done

