#!/bin/bash -x 

# Check special file "lastupload" in log directory to 
# see if there is new log content.  If the internet is reachable, 
# then upload

LOGS=${HOME}/log/
UPHOST=vheavy.com
UPPATH=jim@${UPHOST}:efis-logs/
SSHID=${HOME}/.ssh/id_nexus5
TARFILE=${HOME}/tmp/new-logs.`date +%y%m%d-%H%M%S`.tar

test -f $LOGS/lastupload || touch $LOGS/lastupload
test -d $HOME/tmp || mkdir -p $HOME/tmp
rm -f ${HOME}/tmp/new-logs.*
sudo ping -qc1 $UPHOST > /dev/null 2>&1 && \
find $LOGS -type f -mmin +1 -newer $LOGS/lastupload | \
		xargs tar -cf $TARFILE > /dev/null 2>&1  && \
		test -s $TARFILE && \
		tar -rf $TARFILE ${HOME}/typescript ${LOGS}/permalog.out > /dev/null 2>&1 && \
		sudo ping -qc1 $UPHOST > /dev/null 2>&1 && \
		gzip $TARFILE &&
		scp -pi $SSHID $TARFILE.gz ${UPPATH}/ && \
		touch $LOGS/lastupload


