#!/bin/bash 

function W_ping() { 
	sudo ping -c1 -W1 -q $1 > /dev/null 2>&1
	return $?
}

function W_ssh() { 
	ssh root@$KINDLE_IP $@ 2> /dev/null
	return $?
}

function W_scp() { 
	scp $1 root@$KINDLE_IP:$2 2> /dev/null
	return $?
}

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
sudo killall -9 python python2.7 
export DISPLAY=:1.0
#bash -c "while sleep 1; do i2c ${HOME}/adc-conf/; done" &
python ${LOCALBIN}/j.py &

#sudo ${LOCALBIN}/dateFromGps.sh &

KINDLE_IP=192.168.43.59
while true; do
	sleep 1
	W_ping android-17eb7a23a019699 && KINDLE_IP=android-17eb7a23a019699

	W_ping $KINDLE_IP && W_ssh echo OK || continue

	for f in $SCRIPTS; do 
		echo $f
		W_scp $LOCALBIN/$f $REMOTEBIN/$f
		W_ssh chmod 755 $REMOTEBIN/$f
	done 
	
	# Finally, as long as networking stays up, run main loop
	# verifying VNC server is healthy.  
	while W_ping $KINDLE_IP > /dev/null; do 
		if [ -e $PAUSEDISPLAY ]; then
		    # While paused display flag file is present, kill VNC and
		    # make sure the kindle stays in sleep
			W_ssh am force-stop android.androidVNC
			# This doesn't work, SSH shell needs environment to run input cmd 
			W_ssh 'dumpsys power | grep mWakefulness=Awake &&  \
					input keyevent KEYCODE_POWER' 
		else
			# Otherwise, make sure VNC stays running, and make sure kindle
			# stays awake
			W_ssh $REMOTEBIN/checkrunning.sh VNC $REMOTEBIN/restartvnc.sh
			W_ssh $REMOTEBIN/tapwakeup.sh
		fi 
		sleep 1

		W_ssh $REMOTEBIN/powerwatchdog.sh
		minute=`date +%M`
		if [ "$lastmin" != "$minute" ]; then 
			date
			W_ssh 'dumpsys power | grep mBatteryLevel=' \
				| sed s/mBatteryLevel=// >> $KINDLE_CHARGE_HISTORY
			#${LOCALBIN}/try_upload_logs.sh
		fi
	    lastmin=$minute

	done
	sleep 10
	   
done

