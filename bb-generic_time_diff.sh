#!/bin/sh

##### Meta information
# Linux (Debian-like), FreeBSD
# Xymon script
# Authors : Michel Gravey and Aurelia Bordes (sys.vision)

##### Goal
# Send the offset to xymon server

##### Color explaination
# green : when the offset is inferior or equal to a certain thresold
# yellow : when the offset is superior to a certain thresold
# red : when the command does not work

##### Variables to setup
TEST="time_diff"	# Name of the test
NTP_SERVER="europe.pool.ntp.org"	# Name of the NTP server
TARGET_DIFF=1	# Thresold in seconds : offset above which the test turns yellow


##### Variables
COLOR="yellow"	# Color of the test by default
SYSTEM=`uname -s` # Name of the OS

##### Script
# Get the offset as a float in seconds
DIFF_MS=`/usr/sbin/ntpdate -q $NTP_SERVER | $GREP "time" | $SED -r 's/^.*offset [-+]?([0-9]+\.[0-9]+) sec$/\1/'`
# Get the offset as an integer in seconds
DIFF=`echo $DIFF_MS | $SED -r 's/^([0-9]+)\.[0-9]+$/\1/'`

# If the code execution number is different from 0 then the test turns red
if [ $? -ne 0 ]; then
	COLOR="red"
fi

# If the integer offset is inferior to the thresold then the test turns green
if [ $DIFF -le  $TARGET_DIFF ]; then
	COLOR="green"
fi

##### Send to xymon server
$BB $BBDISP "status $MACHINE.$TEST $COLOR `date` difference : $DIFF_MS sec"
