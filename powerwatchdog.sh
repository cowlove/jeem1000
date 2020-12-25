#!/system/bin/sh

busybox nohup sh -c 'sleep 30 && touch /data/tmp/xxx && dumpsys power | grep mIsPowered=true || poweroff' > /dev/null &
sleep 1
 




