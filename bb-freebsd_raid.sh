#!/bin/sh

#### Meta information
# Original author : Nicolas Lienard
# Modified by : Michel Gravey (sys.vision) 
# BIG BROTHER - WATCH THE RAID
# nli / tay0
#
# For LSI "mpt" / FreeBSD sysctl way
#
#
#####################################################
# INSTALL NOTES (Xymon 4)
#####################################################
# 1. copy bb-raid.sh in your $BBHOME/ext directory
# 2. make it executable : chmod 755 bb-raid.sh
# 3. optionnaly configure TEST variable
#####################################################


#### Variables
TEST="raid"

# CONFIGURE REQUIRED VARIABLES
RES="" 	# Contains the data to send to xymon server

if [ "$BBHOME" = "" ]; then
	echo "BBHOME is not set... exiting"
	exit 1
fi

SYSTEM=`uname -s`


case $SYSTEM in
	FreeBSD)

		COLOR="green"
		num=`sysctl -a | $GREP dev.mpt | $AWK -F. '{print $3}' | $EGREP '^[0-9]+$' | uniq | $WC | $SED -e "s/\ //g"`
		i=0

		while [ $i -ne $num ]
		do
			RES="$RES CONTROLLER $i REPORT :\n"
			while read line
			do
				RES="${RES}$line\n"
			done <<EOF
			`sysctl -a | $GREP "dev.mpt.$i"`
EOF
			RES="${RES}\n"
			status=`sysctl -a | $GREP "dev.mpt.$i.nonoptimal_volumes" | $AWK '{ print $2 }'`
			if [ $status -ne 0 ]; then
				COLOR="red"
				RES="${RES}STATUS : DEGRADED\n"
			else
				RES="${RES}STATUS : OPTIMAL\n"
			fi
			i=$(( $i + 1 ))
		done

		;;
esac

LINE="status+3600 $MACHINE.$TEST $COLOR `date` - raid looks $COLOR `echo ; echo -e $RES`"
$BB $BBDISP "$LINE"             #SEND IT TO BBDISPLAY
