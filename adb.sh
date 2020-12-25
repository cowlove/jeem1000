#!/bin/bash 

ADB="sudo adb"
PING="sudo ping -c1 -W1 -q "
export PATH=$PATH:${HOME}/bin
SCRIPTS="tapwakeup.sh checkrunning.sh restartvnc.sh powerwatchdog.sh"
LOCALBIN=${HOME}/workspace/jeem1000/
REMOTEBIN=/data/tmp/
PAUSEDISPLAY=/tmp/pausedisplay # Flag file, pause display when present
KINDLE_CHARGE_HISTORY=${HOME}/kindleChargeHistory.txt
#sudo systemctl start hciuart
#sudo systemctl start hciuart

rm -f $PAUSEDISPLAY

sudo killall pppd
#sudo killall Xtightvnc
#sudo killall -9 evilwm

tightvncserver -geometry 1024x550 -pixelformat bgr233 -depth 16 :1
sudo killall -9 evilwm python python2.7 
export DISPLAY=:1.0
bash -c "while sleep 1; do i2c ${HOME}/adc-conf/; done" &
python ${LOCALBIN}/j.py &

#sudo ${LOCALBIN}/dateFromGps.sh &

SEENKINDLE=false

while true; do
	# Connectivity step 1: Check kindle shows up on USB hub
	if lsusb | grep -i kindle; then
	#if false | grep -i kindle; then
		echo lsusb found a kindle
		SEENKINDLE=true
	else
		if $SEENKINDLE; then 		
			# Reset the USB bus
			sleep 2
			echo 0 >  /sys/bus/usb/devices/usb1/authorized
			sleep 1
			echo 1 >  /sys/bus/usb/devices/usb1/authorized
			sleep 5
			lsusb | grep -i kindle || sleep 5
			lsusb | grep -i kindle || sleep 5
		fi
		sleep 1
		continue	
	fi

	# Connectivity step 2: Check ADB link is up
	if $ADB shell echo hi | grep hi; then
		echo ADB link OK
	else 
		sudo killall adb
		sudo killall -9 adb
		$ADB kill-server
		continue
	fi

	# Connectivity step 3: check ppp networking is up
	sleep 1
	if $PING 10.0.10.2 > /dev/null; then
	    echo ok
	else
		$ADB shell killall pppd
		sudo killall pppd
		$ADB ppp "shell:pppd nodetach noauth defaultroute /dev/tty" \
			nodetach noauth notty 10.0.10.1:10.0.10.2
		#ping -c 1 192.168.7.1 && route add default gw 192.168.7.1
		$PING 10.0.10.2 || sleep 1 && $PING 10.0.10.2 || sleep 2 && \
		$PING 10.0.10.2 || sleep 5 && $PING 10.0.10.2 || sleep 5 && \
		$PING 10.0.10.2 || sleep 5

		for f in $SCRIPTS; do 
			echo $f
			$ADB push $LOCALBIN/$f $REMOTEBIN/$f
			$ADB shell chmod 755 $REMOTEBIN/$f
		done 
		#continue
	fi

	# Finally, as long as networking stays up, run main loop
	# verifying VNC server is healthy.  
	while $PING 10.0.10.2 > /dev/null; do 
		if [ -e $PAUSEDISPLAY ]; then
		    # While paused display flag file is present, kill VNC and
		    # make sure the kindle stays in sleep
			sudo $ADB shell am force-stop android.androidVNC
			$ADB shell  'dumpsys power | grep mWakefulness=Awake &&  \
					input keyevent KEYCODE_POWER' 
			sleep 6
		else
			# Otherwise, make sure VNC stays running, and make sure kindle
			# stays awake
			$ADB shell $REMOTEBIN/checkrunning.sh VNC $REMOTEBIN/restartvnc.sh > /dev/null
			$ADB shell  'dumpsys power | grep mWakefulness=Asleep &&  \
					input keyevent KEYCODE_POWER' 
			sleep 2
		fi 
		
		$ADB shell  $REMOTEBIN/powerwatchdog.sh
		minute=`date +%M`
		if [ "$lastmin" != "$minute" ]; then 
			date
			$ADB shell 'dumpsys power | grep mBatteryLevel=' \
				| sed s/mBatteryLevel=// >> $KINDLE_CHARGE_HISTORY
			#${LOCALBIN}/try_upload_logs.sh
		fi
	    lastmin=$minute

	done
	   
done

