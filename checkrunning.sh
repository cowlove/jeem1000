#!/system/bin/sh
PSTOKEN=$1
RESTARTCMD=$2

export LD_LIBRARY_PATH=/vendor/lib:/system/lib
export HOSTNAME=android
export BOOTCLASSPATH=/system/framework/core.jar:/system/framework/core-junit.jar:/system/framework/bouncycastle.jar:/system/framework/ext.jar:/system/framework/framework.jar:/system/framework/telephony-common.jar:/system/framework/mms-common.jar:/system/framework/android.policy.jar:/system/framework/services.jar:/system/framework/apache-xml.jar


TIME1=`busybox ps l  | grep $PSTOKEN | grep -v grep | grep -v PPID | sort -k 9 | tail -1 | awk '{print $9}'`   

if test -z $TIME1; then
	$RESTARTCMD
	exit
fi 

sleep 6
 
TIME2=`busybox ps l  | grep $PSTOKEN | grep -v grep | grep -v PPID | sort -k 9 | tail -1 | awk '{print $9}'`

#echo $TIME1 $TIME2
if test -z $TIME1 || test -z $TIME2 || [ $TIME1 = $TIME2 ]; then
    $RESTARTCMD
fi

