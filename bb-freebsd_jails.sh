#!/bin/sh

##### Meta information
# Written for FreeBSD
# Xymon script
# Authors : Michel Gravey and Aurelia Bordes (sys.vision) 

##### Goal
# Send to xymon server the number of subjails

##### Variable to set up
TEST="jails"	# Test name

##### Script
# grep -v invert the sense of matching (take all the lines that don't match the following word)
SERVERNODES=`jls | $GREP -v JID | $WC | $SED -e 's/\ //g'`

##### Send to Xymon server
$BB $BBDISP "data $MACHINE.$TEST $(echo; printf "$TEST : $SERVERNODES\n\n")"
