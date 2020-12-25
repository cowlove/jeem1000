#!/system/bin/sh -x

export LD_LIBRARY_PATH=/vendor/lib:/system/lib
export HOSTNAME=android
export BOOTCLASSPATH=/system/framework/core.jar:/system/framework/core-junit.jar:/system/framework/bouncycastle.jar:/system/framework/ext.jar:/system/framework/framework.jar:/system/framework/telephony-common.jar:/system/framework/mms-common.jar:/system/framework/android.policy.jar:/system/framework/services.jar:/system/framework/apache-xml.jar

dumpsys power | grep mWakefulness=Asleep &&  input keyevent KEYCODE_POWER
am force-stop android.androidVNC    
am start -n android.androidVNC/android.androidVNC.androidVNC 
sleep 3
input tap 20 100

