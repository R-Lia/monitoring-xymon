#!/usr/bin/env python3

#### Meta information
# Written for Ubuntu
# Xymon script
# Authors : Aurelia Bordes and Michel Gravey (sys.vision)

#### Goal
# This script monitors the packages modified in the last x days. The modified packages are divided in 3 categories : install, remove or upgrade.
# Send to xymon server the total number of updated packages the last x days and a HTML table containing the list of these updated packages 
# Send to xymon server the total number of removed packages the last x days and a HTML table containing the list of these removed packages 
# Send to xymon server the total number of installed packages the last x days and a HTML table containing the list of these installed packages 

#### Test color
# clear : no parameter is passed to the script AND the test is not blue
# blue : the test is disabled on the frontend AND there have been no modification in the THREE categories since the time it was disabled OR the category(ies) in which there is/are a change is not passed as a parameter to the script
# yellow : at least one change in at least one of the three categories AND in the parameter passed to the script is the name (upgrade/install/remove) of at least one of modified category
# red : the shell command does not work


######Modules
import os
import subprocess
import csv
import datetime
import hashlib
import sys
import argparse

###### Environment variables 
bbbin=os.environ['BB']
bbdisp=os.environ['BBDISP']
bbmachine=os.environ['MACHINE']
bbtmp=os.environ['BBTMP']

###### Variables to setup
dpkg_log="/var/log/dpkg.log*" # Path to apt log files
test="apt_history"  # Name of the test
period=2    # Number of days from which we want to check modified packages
file_name="original"    # Beginning of the file name storing the different timestamps
file_name_blue="timestamp_blue.txt"    # Name of the file to store timestamp_blue and status_blue

###### Other variables
color="clear"  # color of the test by default
bbmachine_name=bbmachine # if MACHINE is not the displayed name on xymon board
msg=""  # message that appear just above each HTML table
has_changed_once=False # Change to True when there is a change in a category AND this category is passed as a parameter to the script. useful to change color
status_blue="initial" # If the test is not blue then set to "refresh" else keep "initial". Stored in a file with timestamp_blue. Useful to determine timestamp_blue because it allows us to know if the test was blue an iteration before the current color. 

now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")   # Current date and imein string. 
now_tz=datetime.datetime.now(datetime.timezone.utc).astimezone().tzname() # Current timezone 
thresold_date=(datetime.datetime.now() - datetime.timedelta(days=period)).strftime("%Y-%m-%d %H:%M:%S")    # Date and time "last_change-days" days before now in string. We display the modified packages since "thresold_date"

# Booleans useful for determining if we have to change the color in function of the parameter(s) given
upgrade=False
install=False
remove=False

# HTML table that will be send to xymon server. It contains datetimes and packages that were modified since the "last_change_days" days
table="<h3>%s run at %s %s on %s</h3><br><br>  " %(test, now, now_tz, bbmachine_name)
table +="<h3> Packages modified in the last %i days</h3><br><br>  " %period

pkg_modified={'install':0, 'remove':0, 'upgrade':0} # Dictionnary that contains the total number of modified packages for each category in the last "period" days

#####Functions
# Function to activate when there has been a change (= when the 2 hashes are different or when the file containing the original hash does not exist). 
def has_changed(timestamp_last, hash_last_line, history_type, blue_stdout, timestamp_blue, status_blue, check_parameter, file_name, file_name_blue):

    # Create or overwrite a file storing timestamp_last and hash_last_line on 2 lines
    file = open("%s/%s_%s.txt"%(bbtmp,file_name, history_type), "w+") 
    file.write("%s\n%s"%(timestamp_last, hash_last_line))
    file.close()

    # If the test is blue then reactivate the test
    if (len(blue_stdout)!=0):
        reactivate=subprocess.Popen("%s %s 'enable %s.%s'"%(bbbin, bbdisp, bbmachine, test),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)
    
    # Case #2 : update status_blue once to reset date / time at next acknowledgment (works an iteration before case #1)
    if (status_blue == "initial"):
        status_blue="refresh"
        file=open("%s/%s" %(bbtmp,file_name_blue),"w+")
        file.write("%s\n%s"%(timestamp_blue,status_blue))
        file.close()
    return(True)


###### Process the command line options
# Create a parser 
parser = argparse.ArgumentParser()

# Add an optional positional argument, nargs is the number of times the argument can be used
parser.add_argument("category",help="a list separated by comma of the categories (install,remove,upgrade) you want to monitor", nargs='?')

# Add an optional flag with a mandatory value
parser.add_argument("-r",help="alias of the host in hosts.cfg")

# Parse the argument and place them in a argparse.Namespace object:
arguments=parser.parse_args()

# If the optional flag r is initialized then change bbmachine_name, the name used to interrogate xymondboard
if arguments.r is not None:
    bbmachine_name=arguments.r
#    print(bbmachine_name)

# If there is an optional positional argument 
if arguments.category is not None:
    category_list=arguments.category.split(",")
#    print(category_list)

    # Set the corresponding boolean(s) to True
    if "upgrade" in category_list:
        upgrade=True
    if "install" in category_list:
        install=True
    if "remove" in category_list:
        remove=True

check_parameter={'upgrade': upgrade,'remove': remove,'install': install}   # Dictionnary with the 3 monitored elements as keys and a boolean as their value that says if it is in the parameters of the script


######Script

## Part 1 : Processing everything that is blue-related
# Check if the test is currently blue or if test is blue but without disabled status (meaning : not really "blue")
blue=subprocess.Popen("%s %s 'xymondboard host=%s test=%s' | head -n 1 | awk -F'\|' '{ print $3\",\"$9 }' | grep blue | grep -vE '^blue,0$'"%(bbbin, bbdisp, bbmachine_name, test),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)
blue_stdout = blue.communicate()[0] 

# If a file containing timestamp blue and status_blue exists 
if (os.path.exists("%s/%s" %(bbtmp,file_name_blue))):
    # Store timestamp_blue and status_blue in 2 variables
    file=open("%s/%s" %(bbtmp,file_name_blue),"r")
    file_blue=file.readlines()
    timestamp_blue = file_blue[0].rstrip("\n")
    status_blue = file_blue[1].rstrip("\n")
    file.close()

else :
    timestamp_blue=now

# If the test is blue (=disabled)
if (len(blue_stdout)!=0):  
    
    # If the file containing timestamp blue and status_blue does not exist or if it was not blue an iteration before (status_blue=refresh)
    if (not os.path.exists("%s/%s" %(bbtmp,file_name_blue)) or status_blue == "refresh"):
        # Create a file storing the current datetime and status : first iteration as blue or reset date / time if acknowledged first time
        status_blue = "initial"
        timestamp_blue = now
        
        # Create or overwrite the file containing timestamp_blue and status_blue
        file=open("%s/%s" %(bbtmp,file_name_blue),"w+")
        file.write("%s\n%s"%(timestamp_blue,status_blue))
        file.close()
        # To display this run latest packages changes with the new timestamp reference

# First iteration as other than blue: we create a timestamp_blue file with the current time as reference
# Case #1: if the test is not disabled, update status_blue once to reset date / time at next acknowledgment (works even when no changes)

# If the test is not currently blue and status_blue is set to initial (=the test was blue an iteration before)
elif ( (len(blue_stdout)==0) and status_blue == "initial"):
    status_blue="refresh"
    # We keep original date / time reference from previous acknowledgment 
    # At next acknowledgment, with status_blue=refresh, the date / time reference will be reset
    file=open("%s/%s" %(bbtmp,file_name_blue),"w+")
    file.write("%s\n%s"%(timestamp_blue,status_blue))    
    file.close()


##Part 2 : The main loop
# Main loop for the 3 keys in check_parameter sorted in acsending order (install, remove, upgrade)
for history_type in sorted(check_parameter.keys()):

    # Get the list of the corresponding category packages
    cmd= '''zgrep -hE '[0-9]{2}:[0-9]{2}:[0-9]{2} %s ' %s''' %(history_type,dpkg_log)
    process = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate() 

    # If there is a problem with the execution of cmd then set the test color to red, send the test color and stderr to xymon server and exit the code
    if (process.returncode > 1):
        color="red"
        os.system("%s %s 'status %s.%s %s %s\n\n'" %(bbbin, bbdisp, bbmachine, test, color, stderr))
        sys.exit()

    # Preprocess stdout
    stdout=stdout.replace(" %s "%history_type, ",") # Replace upgrade/install/remove by a comma to have <datetime>, <package> 
    stdout=stdout.strip()  # Delete the last empty line
    
    # Create a list from stdout and sort it in ascending order
    liste=stdout.split("\n")
    liste=sorted(liste)
    m=len(liste)    # useful later in the script

    # Get the last element of the list and hash it with md5
    last_line=liste[-1]
    hash_last_line=hashlib.md5(last_line.encode()).hexdigest() 
    
    # Store the new reference timestamp 
    timestamp_last=last_line.split(",")[0]

    # If the category is passed as a parameter to the script then check different conditions to set the appropriate color
    if (check_parameter["%s" %history_type]): 
    
        # If a file containing a hash and a timestamp from a previous iteration of this script exists
        if (os.path.exists("%s/%s_%s.txt" %(bbtmp,file_name,history_type))):

            # Get the original hash and timestamp
            file = open("%s/%s_%s.txt"%(bbtmp,file_name,history_type), "r")
            hash_original = file.readlines()[1]     # The hash is stored on the second line
            file.close()

            # If the 2 hashes are different
            if (hash_last_line != hash_original):
                # Function to invoke when there has been a change 
                has_changed(timestamp_last, hash_last_line, history_type, blue_stdout, timestamp_blue, status_blue, check_parameter, file_name,file_name_blue)
                has_changed_once=True

        # If there are no file containing the original hash and timestamp (=first iteration) then we consider that there has been a change
        else:
            # Function to invoke when there has been a change 
            has_changed(timestamp_last, hash_last_line, history_type, blue_stdout, timestamp_blue, status_blue, check_parameter, file_name,file_name_blue)
            # Reminder for the loop if hash as change at least once
            has_changed_once=True

        # If the hash has changed or the test is not blue then the color is changed to yellow
        if (has_changed_once or len(blue_stdout)==0):
            color = "yellow" 
        
        if (last_line==""):
            msg="%s : No change" %history_type

        # If changes occurs after last acknowledgment 
        if (timestamp_last > timestamp_blue): 
            msg ="%s : new change(s) since %s (after last acknowledgment)" %(history_type, timestamp_blue)
        else:
            msg ="%s : latest change(s) on %s (apt activity)" %(history_type, timestamp_last) 

    # If the category is not passed as an argument to the script
    else :
        msg ="%s is not monitored" %(history_type) # Generate a message saying that the category is not monitored


    # Add the message before the corresponding HTML table
    table += "%s <br><br>" %msg

    # Get the index of the line where timestamp < thresold_date
    boo=False   # Boolean that comes true when the timestamp in liste is inferior to thresold_date (=30 days before now)
    i=0
    while (not boo and i < m and m>0):  # While we are not considering packages that were modified last 30days and have not an indice out of range and we have zgrep something (ie liste not empty)
        boo = liste[i].split(",")[0] > thresold_date
        i+=1

    # If boo becomes true (= there are packages of the considered category that were modified since thresold_date    
    if boo :
        num_line=i-1
        pkg_modified["%s" %history_type]=(m - num_line)  # Fill pkg_modified with the number ofthe appropriate packages since thresold_date

        # Start the HTML table of this category : Put the header row
        table += "<table border=1 cellpadding=10> <tr> <th> Timestamp </th> <th> packages (%s) </th> </tr>" %history_type

        # Put the sorted list of upgraded/installed/removed packages last 30 days in the corresponding HTML table 
        for j in range(num_line, m):
            split_comma=liste[j].split(",") # Split each element of the list, the first one is the timestamp, the second the package

            # If the category is passed as a parameter to the script 
            if (check_parameter["%s" %history_type]): 
                # If the timestamp is more recent that the timestamp of the latest acknowledgment then put it in italic in the HTML table
                if (split_comma[0] > timestamp_blue):
                    table +="<tr> <td> <i> %s </i> </td> <td> <i> %s </i> </td> </tr>" %(split_comma[0], split_comma[1])

                # If the timestamp is older add it to the table with no extra features
                else:
                    table +="<tr> <td> %s </td> <td> %s </td> </tr> " %(split_comma[0], split_comma[1])
           
           # If the category is not passed as an argument then fill the HTML table with no extra feature
            else:
                table +="<tr> <td> %s </td> <td> %s </td> </tr> " %(split_comma[0], split_comma[1])
            # If the package has already been acknowledged then put it with no extra feature in the HTML table

        # Close the HTML table of this category
        table += "</table><br><br>"

# If the test is blue and has_changed_once=False after the 3 iterations then set the color to blue
if (len(blue_stdout)!=0 and not has_changed_once):
    color="blue"

#DEBUG
#print(table)
#print(pkg_modified)
      
#####Send to Xymon server
os.system("%s %s 'status %s.%s %s %s\n\n'" %(bbbin, bbdisp, bbmachine, test, color, table))
os.system("%s %s 'data %s.%s\n%s_install : %s\n%s_remove : %s\n%s_upgrade : %s\n\n'" %(bbbin, bbdisp, bbmachine, test, test, pkg_modified['install'], test, pkg_modified['remove'], test, pkg_modified['upgrade']))

