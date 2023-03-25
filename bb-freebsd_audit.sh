#!/bin/sh

#### Meta information
# Written for FreeBSD
# Xymon script
# Author : Aurelia Bordes (sys.vision)

#### Goal
# Send the output of pkg audit to xymon server

#### Color explaination
# green : no vulnerabilities found by pkg audit
# blue : test disabled via xymon frontend and no change in the output of pkg audit since it was disabled
# yellow : at least one vulnerability found by pkg audit when the test is not disabled or a change between the vulnerabilities found by pkg audit now and the vulnerabilities found when the test was disabled

#### Variables to set up
TEST="pkg_audit"	# Name of the test
FILENAME="pkg_audit"	# Name of the file to store the hash
MACHINENAME=$MACHINE	# Name of the client that is displayed on the frontend. Useful to call xymondboard who do not recognize the host if there is an alias. By default it is the environment variable MACHINEDOTS*
PATH2PKG="/usr/sbin/pkg"	# Path to the pkg command

#### Variables
COLOR="green"
NB_PROBLEM=0
NB_PKG=0

#### Function
help() {
	cat << EOF
        Usage: [-h] -r [hostname]

        optional parameters:

        -r [hostname]  Alias of the host given in the hosts.cfg 

        -h, --help      Display this help message and exit.

EOF

}	

#### Process the command line options
while getopts "hm:" options;
do
	case $options in 
		h)
			help
			exit
			;;
		m)
			if ["`echo ${OPTARG} | egrep '^([.-_a-zA-Z0-9])+$'`" == '']; then
				echo "Invalid hostname parameter"
				exit
			else
				MACHINENAME="${OPTARG}"
			fi
			;;
		*)
			help
			exit
			;;
	esac	
done	

#### Script
if [ ! -e "$PATH2PKG" ]; then
	COLOR="red"
	$BB $BBDISP "status $MACHINEDOTS.$TEST $COLOR `date` The command pkg audit does not exists"
	exit
fi 

# Store the output of pkg audit in a variable
#PKG_AUDIT="`/usr/sbin/pkg audit`"
PKG_AUDIT="`$PATH2PKG audit`"

# Hash this output
HASH_AUDIT="`echo $PKG_AUDIT | md5`"

# Count the number of line of the output
COUNT=`echo "$PKG_AUDIT" | $WC | $SED -e 's/\ //g'`

# If a file containing the hash of the output of pkg audit already exists
if [ -e "$BBTMP/$FILENAME.txt" ]; then

	# If the 2 hashes are different then change the color to yellow and store the new hash
	if [ "`cat $BBTMP/pkg_audit.txt`" != "$HASH_AUDIT" ]; then
		printf "$HASH_AUDIT" > "$BBTMP/$FILENAME.txt"
		COLOR="yellow"

	# If the two hashes are not different 
	else
		# Ask xymon server if the test is blue
		BLUE=`$BB $BBDISP 'xymondboard host=$MACHINENAME test=$TEST' | head -n 1 | $AWK -F'|' '{ print $3","$9 }' | $GREP blue | $GREP -vE '^blue,0$'`

		# If the test is blue then keep blue
		if [ "$BLUE" != "" ]; then
			COLOR="blue"

		# If the test is not blue	
		else
			# If the number of line is different from 1, then it means there is a problem
			if [ $COUNT -ne 1 ]; then
				COLOR="yellow"
			fi
		fi	
	fi
# If the file does not exist
else
	# Create a file to store the hash
	printf "$HASH_AUDIT" > "$BBTMP/$FILENAME.txt"

	# If the number of line is different from 1, then it means there is a problem
	if [ $COUNT -ne 1 ]; then
		COLOR="yellow"
	fi
fi

# If there is a problem, then parse the last line of the output to get the total number of problems and the total number of packages with problems
if [ $COUNT -ne 1 ]; then 
	#NB_PROBLEM=`echo "$PKG_AUDIT" | tail -n 1 | awk '{print $1}'`
	NB_PROBLEM=`echo "$PKG_AUDIT" | tail -n 1 | awk '{print $1}'`
	NB_PKG=`echo "$PKG_AUDIT" | tail -n 1 | awk '{print $4}'`
fi

#### Send to Xymon server
$BB $BBDISP "status $MACHINEDOTS.$TEST $COLOR `date` 
$PKG_AUDIT"
$BB $BBDISP "data $MACHINEDOTS.$TEST $(echo; printf "${TEST}_problem : $NB_PROBLEM\n${TEST}_pkg : $NB_PKG\n\n")"
