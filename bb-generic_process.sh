#!/bin/sh

##### Meta information
# OS : Linux (Debian-like), FreeBSD 
# Author : Aurelia Bordes (sys.vision) 

##### Goal

##### Variables to set up
TEST="pstates"	# Test name

GREP='grep'
AWK='awk'
WC='wc -l'
SED='sed'
PS='ps ax'

##### Variables
PROCESS_D=0	#Number of process in disk wait
PROCESS_I=0	#Number of idle process
PROCESS_L=0	#Number of process waiting to acquire a lock
PROCESS_R=0	#Number of runnable process
PROCESS_S=0	#Number of process sleeping for less than 20sec
PROCESS_T=0	#Number of stopped process
PROCESS_W=0	#Number of idle interrupted threads
PROCESS_Z=0	#Number of zombie process

##### Script
PS_RESULT=`$PS`	# To avoid running ps ax multiple times

PROCESS_D=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP D | $WC | $SED s/\ //g`
PROCESS_I=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP I | $WC | $SED s/\ //g`
PROCESS_L=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP L | $WC | $SED s/\ //g`
PROCESS_R=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP R | $WC | $SED s/\ //g`
PROCESS_S=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP S | $WC | $SED s/\ //g`
PROCESS_T=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP T | $WC | $SED s/\ //g`
PROCESS_W=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP W | $WC | $SED s/\ //g`
PROCESS_Z=`echo "$PS_RESULT" | $AWK '{print substr($3,1,1)}' | $GREP Z | $WC | $SED s/\ //g`

#DEBUG
#echo "##########START"
#echo $TEST
#echo "###############"
#echo "`date` $BB $BBDISP \"data $MACHINE.$TEST $(echo; echo -e "\n${TEST}d : $PROCESS_D\n${TEST}i : $PROCESS_I\n${TEST}l : $PROCESS_L\n${TEST}r : $PROCESS_R\n${TEST}s : $PROCESS_S\n${TEST}t : $PROCESS_T\n${TEST}w : $PROCESS_W\n${TEST}z : $PROCESS_Z\n\n")\""
#echo "###############"
#echo "D : $PROCESS_D"
#echo "I : $PROCESS_I"
#echo "L : $PROCESS_L"
#echo "R : $PROCESS_R"
#echo "S : $PROCESS_S"
#echo "T : $PROCESS_T"
#echo "W : $PROCESS_W"
#echo "Z : $PROCESS_Z"
#echo "###############"
#echo "$PS_RESULT"
#echo "############END"

###### Send to xymon server
$BB $BBDISP "data $MACHINE.$TEST $(echo; echo -e "\n${TEST}d : $PROCESS_D\n${TEST}i : $PROCESS_I\n${TEST}l : $PROCESS_L\n${TEST}r : $PROCESS_R\n${TEST}s : $PROCESS_S\n${TEST}t : $PROCESS_T\n${TEST}w : $PROCESS_W\n${TEST}z : $PROCESS_Z\n\n")"
