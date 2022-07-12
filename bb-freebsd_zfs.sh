#!/bin/sh
# Revision History:
# 1. Mike Rowell <Mike.Rowell@Rightmove.co.uk>, original
# 2. Uwe Kirbach <U.Kirbach@EnBW.com>
# 3. T.J. Yang: add in some comments.
# 4. Vernon Everett <everett.vernon@gmail.com : Added check for old snapshots
#                                             : Added graphing data
# 5. FreeSoftwareServers <admin@freesoftwareservers.com>: 
# Update to new "zpool list -h" format
# Add Available/Free to table
# Full "zpool status" always displayed
# Set DEGRADED=RED
# DISKYELL=90 & DISKRED=95
# 6. Michel Gravey and Aurélia Bordes (sys.vision)

##### Default variables that can be modified by optional parameters  
DISKYELL=90	# Percentage from which the CAP_COLOR becomes yellow
DISKRED=95	# Percentage from which the CAP_COLOR becomes red
SNAPRED=90      # Days old
SNAPYELL=60     # Days old
SNAPCOL=true    # Set to true if snapshot age should effect test colour
CHECKSNAPS=true # Set to true to do snapshot checking

##### Variables
TEST="zfs"	# test name
COLOR="green"
FIRST_LINE="zfs - okay"
FIRST_LINE_HEALTH="okay"
FIRST_LINE_CAP="okay"

help() {
	cat << EOF

    Usage: ${TEST} [-h] [-diskyell NUMBER] [-diskred NUMBER] [-snapyell NUMBER] [-snapred NUMBER] [-snapcol BOOLEAN] [-checksnaps BOOLEAN]

        Optional parameters:

        -h	      		Display this help message and exit.
	
	-diskyell NUMBER 	Percentage of capacity from which the CAP_COLOR becomes yellow. Default : 90
	
	-diskred NUMBER		Percentage of capacity from which the CAP_COLOR becomes red. Default : 95 

	-snapyell NUMBER 	Number of days from which the LINE_COLOR becomes yellow. Default : 60

	-snapred NUMBER 	Number of days from which the LINE_COLOR becomes red. Default : 90

	-snapcol BOOLEAN	Say if the snapshot age should affect the test color (LINE_COLOR). Default : true 

	-checksnaps BOOLEAN	Say if snapshots are checked. Default : true

	
EOF
}

#### Process the command line options
# This script uses long arguments options and getopts does not support them so convert them to short options
for arg in "$@"; do
  shift
  case "$arg" in
    "-diskyell") set -- "$@" "-y" ;;
    "-diskred") set -- "$@" "-r" ;;
    "-snapyell")   set -- "$@" "-s" ;;
    "-snapred")   set -- "$@" "-p" ;;
    "-snapcol")   set -- "$@" "-c" ;;
    "-checksnaps")   set -- "$@" "-k" ;;
    *)        set -- "$@" "$arg"
  esac
done

# Parse short options with getopts
OPTIND=1
while getopts "hy:r:s:p:c:k:" opt
do
  case "$opt" in
    "h") help && exit ;;	
    "y") DISKYELL="${OPTARG}" ;;
    "r") DISKRED="${OPTARG}" ;;
    "s") SNAPYELL="${OPTARG}" ;;
    "p") SNAPRED="${OPTARG}" ;;
    "c") SNAPCOL="${OPTARG}" ;;
    "k") CHECKSNAP="${OPTARG}" ;;
    "?") exit 1 ;;
  esac
done
shift $(expr $OPTIND - 1) # remove options from positional parameters

echo "DISKYELL = $DISKYELL"
echo "DISKRED = $DISKRED"
echo "SNAPCOL = $SNAPCOL"

# TEMP DEFS
#AWK='awk'
#GREP='grep'
#WC='wc -l'

#What: beautify the page display by html code.
STRING="<table border=1 cellpadding=10><tr><th></th><th>Zpool Name</th><th>Status</th><th>Allocated</th><th>Free</th><th>Capacity</th></tr>"
#What: a loop to parse output of "zpool list -H" output.
# bash-3.00# zpool list
# NAME                    SIZE    USED   AVAIL    CAP  HEALTH     ALTROOT
# mypool                 33.8G   84.5K   33.7G     0%  ONLINE     -
#####UPDATE####zpool
#
#:# zpool list
#NAME     SIZE  ALLOC   FREE  EXPANDSZ   FRAG    CAP  DEDUP  HEALTH  ALTROOT
#raid-z  18.1T  13.6T  4.54T         -     0%    74%  1.00x  ONLINE  -
# bash-3.00# zpool list -H
# mypool  33.8G   84.5K   33.7G   0%      ONLINE  -
# bash-3.00#

convertB_human() {
NUMBER=$1
for DESIG in Bytes KB MB GB TB PB
do
   [ $NUMBER -lt 1024 ] && break
   NUMBER=$(( NUMBER / 1024 ))
done
printf "%d %s\n" $NUMBER $DESIG
}

if [ !  -e "/dev/zfs" ]; then
	echo "ZFS unavailable. Quitting !"
	exit 1
fi

while read name size alloc free ckpoint expandsz frag cap dedup health altroot 
do
	LINE_COLOR="green"
	# Health of a pool according to the HEALTH column of zpool list changes the value of HEALTH_COLOR
	if [ "${health}" = "ONLINE" ]; then
		HEALTH_COLOR="green"
	else
		HEALTH_COLOR="red"
	fi


# Capacity a pool according to the CAP column of zpool list changes the value of CAP_COLOR
CAP_COLOR="green"
cap=`echo ${cap} | cut -d% -f1`
if [ "${cap}" -ge $DISKYELL ]; then
	CAP_COLOR="yellow"
elif [ "${cap}" -gt $DISKRED ]; then
	CAP_COLOR="red"
fi
#DATA=$(printf "${name} : ${cap}\n${DATA}")
DATA="${DATA}\n[zfs,${name}.rrd]\nDS:pct:GAUGE:600:0:U ${cap}"

# DEBUG
#echo "data : $DATA"

# Determine the line colours
[ "$HEALTH_COLOR" = "yellow" -o "$CAP_COLOR" = "yellow" ] && LINE_COLOR="yellow"
[ "$HEALTH_COLOR" = "red" -o "$CAP_COLOR" = "red" ] && LINE_COLOR="red"

# Determine the messages
[ "$HEALTH_COLOR" = "red" ] && FIRST_LINE_HEALTH=${health}
[ "$CAP_COLOR" = "yellow" -a "$FIRST_LINE_CAP" != "full" ] && FIRST_LINE_CAP="nearly full"
[ "$CAP_COLOR" = "yellow" ] && FIRST_LINE_CAP="full"

#Determine the final colour status
[ "$LINE_COLOR" = "yellow" -a "$COLOR" != "red" ] && COLOR="yellow"
[ "$LINE_COLOR" = "red" ] && COLOR="red"

STRING="`echo ${STRING}`<tr><td>&${LINE_COLOR}</td><td>${name}</td><td>${health}</td><td>${alloc}</td><td>${free}</td><td>${cap} %</td></tr>"
done <<EOF 
	$(zpool list -H) 
EOF

STRING="`echo ${STRING}`</table><br><br>"
STRING="`echo ${STRING} && zpool status`"
FIRST_LINE="zfs - Health Report: $FIRST_LINE_HEALTH - Capacity Report: $FIRST_LINE_CAP"

# Snapshot check
if [ "$CHECKSNAPS" = "true" ]
then
	NOW="`date +%s`" 
	SNAPCHECK="`zfs list -H -t snapshot`"
	if [ -z "$SNAPCHECK" ] # True if $SNAPCHECK length is zero
	then
		SNAPTABLE="<br><br>&green No snapshots found"
	else
		SNAPTABLE="<br><br><table border=1 cellpadding=10><tr><th></th><th>Dataset</th><th># of snapshots</th><th>Max age</th><th>Size</th></tr>"
		while read snapuniq
		do
			MAX_AGE=0
			SNAPCOUNT=0
			while read SNAPSHOT CREATION
			do
				SNAPCOUNT=$((SNAPCOUNT+1))
				LINE_COLOR=green
				SNAPREDS=$((SNAPRED*43200))
				SNAPYELLS=$((SNAPYELL*43200))
				AGES=$((NOW-CREATION)) # AGES=Age in seconds
				[ $AGES -gt $MAX_AGE ] && MAX_AGE=$AGES
			done << EOF
			$(zfs list -H -p -r -d1 -t snapshot -o name,creation $snapuniq)
EOF
			[ $MAX_AGE -gt $SNAPYELLS ] && LINE_COLOR=yellow
			[ $MAX_AGE -gt $SNAPREDS ] && LINE_COLOR=red
			[ $MAX_AGE -gt 120 ] && AGE=$((MAX_AGE/60))&& AGE="$AGE Minutes"
			[ $MAX_AGE -gt 7200 ] && AGE=$((MAX_AGE/3600)) && AGE="$AGE Hours"
			[ $MAX_AGE -gt 172800 ] && AGE=$((MAX_AGE/86400)) && AGE="$AGE Days"
			FULL_SIZE=$(zfs list -H -r -d0 -o usedsnap $snapuniq)
			SNAPTABLE="`echo ${SNAPTABLE}`<tr><td>&${LINE_COLOR}</td><td>${snapuniq}</td><td>${SNAPCOUNT}</td><td>${AGE}</td><td>${FULL_SIZE}</td></tr>"
			if [ "$SNAPCOL" = "true" ] #Only if true will it effect test colour
			then
				if [ "$COLOR" != "red" ] # If it's already red, it's not getting any worse
				then
					[ "$LINE_COLOR" != "green" ] && COLOR=$LINE_COLOR
				fi
			fi
		done<<EOF 
		$(zfs list -H -t snapshot | $AWK -F@ '{print $1}' | uniq)
EOF
		SNAPTABLE="`echo ${SNAPTABLE}`</table><br><br>"
		STRING="$STRING <br><br><B>SNAPSHOT STATUS</B> $SNAPTABLE"
	fi
fi

#### Sent out the final bb message to hobbit server.
$BB $BBDISP "status $MACHINE.$TEST $COLOR `date` $FIRST_LINE $STRING"
$BB $BBDISP "data $MACHINE.trends $(echo; echo -e "${DATA}\n\n")"
