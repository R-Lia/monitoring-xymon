#!/bin/sh
#set -xv
#####################################################################
#
#       Name:                   Padraig Lennon (padraig.lennon@pioneerinvestments.com) 
#	Modified by		Aurelia Bordes and Michel Gravey (sys.vision)	
#       Script Description:     Check the SSH tunnels to Hobbit/Xymon server 
#                                       Please leave reference to original author.

###########################################################################
#       Constants/Global variables
###########################################################################

PROGNAME=$(basename $0)                 # Script Name
TEST=tunnel                             # Hobbit/Xymon test name
SSH_PORT="22"				# Default SSH port
REMOTE_SERVER=""			# No useful default (host or IP of remote ssh server)
IDENTITY_PARAM=""			# No useful default (path to the private ssh idendity key)
COLOR="green" 				# Default color
MSG="$TEST status for host $MACHINE"	# Default message to send to xymon status channel 

###########################################################################
#       Functions
###########################################################################

#####
#       Function for exit due to fatal program error
#       Arguments=1
#       Argument 0: string containing descriptive error message
#####
error_exit()
{
	local ERR_MSG

	ERR_MSG="Error: ${1}"
	echo "`date` - ${ERR_MSG}" >&2
	exit 255
}



#####
#       Function for printing warning messages
#       Arguments=1
#       Argument 0: string containing descriptive warning message
#####
warning()
{
	local WARN_MSG

	WARN_MSG="Warning: ${1}"
	echo "`date` - ${WARN_MSG}" >&2
}



#####
#       Function for printing script steps
#       Arguments=1
#       Argument 0: string containing descriptive step message
#####
print_step()
{
	local STEP_MSG

	STEP_MSG="#----> ${1}"
	echo ${STEP_MSG}
}



#####
#       Function to perform exit if interrupt signal is trapped
#       Arguments=0
#####
int_exit()
{
	echo "${PROGNAME}: Aborted by user"
	exit 255
}




#####
#       Function to display help message for program
#       No arguments
#####
help()
{
	cat <<EOF

	Check ssh-tunnels to ssh server hosting Xymon server


	Usage: ${PROGNAME} [-h] [number]

	Required parameters:

	-r [hostname]	Remote xymon server hostname		

	Optional parameters:

	-h, --help      Display this help message and exit.

	-p [port]	Remote server ssh port number

	-i [path]	path to the private ssh key

	Example(s):

	${PROGNAME}


	Exit Codes:
	0       Success
	255     Error


	Initial author: Padraig Lennon
	Updated to plain shell for client to ssh server by Aurelia Bordes and Michel Gravey (Sys.Vision SAS 2021)

EOF
}


#####
#       Function to restart the ssh tunnel
#####
restart_tunnel()
{
	#   Restarting the Tunnel
	ssh -fnNL 1984:localhost:1984 $IDENTITY_PARAM -o StrictHostKeyChecking=no -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null -p $SSH_PORT $REMOTE_SERVER
	if [ $? -ne 0 ] ; then
		MSG="&red Tunnel to $REMOTE_SERVER is down.. Restart attempt failed"
		COLOR=red
	else
		MSG="&yellow Tunnel to $REMOTE_SERVER recently restarted"
		COLOR=yellow
	fi

}

#####   USER DEFINED FUNCTIONS  ######################
###########################################################################
#       Check command line parameters
###########################################################################

# Trap INT signals and properly exit

trap int_exit INT



# Process command line arguments
#       Parameters with arguments divide with : i.e. for option o use o:
#       Parameters with no arguments add the option after the h. no extra :
while getopts "hr:p:i:" opt; do
	case $opt in
		h)     
			help
			exit
			;;
		r)	
			r="${OPTARG}"
			;;
		p)	
			p="${OPTARG}"
		 	;;
		i)	
			i="${OPTARG}"
		 	;;
		*)     
			help
			error_exit "Wrong parameter passed"
			;;
	esac
done

shift $((OPTIND-1))

# If the -r parameter is not passed to the script then display the help message and exit the script
if [ -z "${r}" ] || [ "`echo $r | $EGREP '^([-_.a-zA-Z0-9])+$'`" == "" ]; then 
	help
	error_exit "You need to pass the hostname of xymon server as an argument : ${r}"
else
	REMOTE_SERVER=$r
fi



###########################################################################
#       Main Body of Script
###########################################################################
if [ "`uname`" = "FreeBSD" ]; then 
	PS="ps awwx -J0"
fi

# If the optional parameter -p is passed to the script and that the value is formatted like a port then set the SSH_PORT to this value
if [ ! -z "${p}" ] && [ "`echo $p | $EGREP '^[1-9][0-9]{1,4}$'`" != "" ]; then 
	SSH_PORT=$p
elif [ ! -z "${p}" ]; then
	help
	error_exit "Wrongly formatted port number option: ${p}"
fi


# If the optional parameter -i is passed to the script and that the value is formatted like a path then setcreate a value that will be used in the ssh commad 
if [ ! -z "${i}" ] && [ "`echo $i | $EGREP '^(\/[-_.a-zA-Z0-9]+)+$'`" != "" ]; then 
	IDENTITY_PARAM="-i $i"
elif [ ! -z "${i}" ]; then
	help
	error_exit "Wrongly formatted path string option: ${i}"
fi

# Count the number of SSH tunnels
COUNT=`$PS | $GREP 'ssh -fnNL 1984'| $GREP "\-p $SSH_PORT $r$" | $WC | $SED -e "s/\ //g"`

# If there are no SSH tunnel then set the color to yellow and restart a tunnel
if [  $COUNT -eq 0 ] ; then
	COLOR=yellow
	#   Restarting the Tunnel
	restart_tunnel 

# If there are more than 1 SSH tunnel then kill all the tunnels and restart the tunnel
elif [ $COUNT -gt 1 ] ; then
	for PROCESS in `$PS|$GREP "ssh -fnNL 1984"| $GREP "\-p $SSH_PORT $r$" | $AWK '{print $1}'`
	do
		kill $PROCESS
	done

	#   Restarting the Tunnel
	restart_tunnel 

# If there is exactly 1 SSH tunnel then change the MSG to send to xymon server 
else
	MSG="&green SSH Tunnel to $REMOTE_SERVER ok"
fi


###### Send to xymon server
$XYMON $XYMSRV "status $MACHINE.$TEST $COLOR `date`

${MSG}
"

exit
