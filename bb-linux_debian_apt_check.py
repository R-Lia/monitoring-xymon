#!/usr/bin/env python3

######Characteristics
# written for Linux (Ubuntu)
# Xymon script
# Python script
# Author : Aurelia Bordes (sys.vision)

######Goal
# This script monitors the available updates in specific repositories when a parameter is passed to the script or in all the repositories if there is no parameter. 

###### Color explaination
# green : no updates are available for ALL repo monitored AND the test was not blue before.
# blue : the test is disabled on the frontend AND there are no update available in ALL the repo monitored since the time it was disabled 
# yellow : at least one change in at least one of the repo monitored 

######Modules
import os
import subprocess
import csv
import datetime
import hashlib
import sys
import re
import argparse


###### Environment variables 
bbbin=os.environ['BB']
bbdisp=os.environ['BBDISP']
bbmachine=os.environ['MACHINE']
bbtmp=os.environ['BBTMP']

###### Variables to setup
test="apt_check"  # Name of the test

###### Other variables
color="green"  # color of the test by default (=no update available)
bbmachine_name=bbmachine # if MACHINE is not the displayed name on xymon board (by default equal to bbmachine)
total=0 # Total number of updates available
has_changed_yellow=False # Change to True, if there is at least one change in one of the repo monitored. 
n=0         # length of the list of repositories passed as a parameter to the script = number of repositories to monitor. By default, at 0 which means all repositories 

now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")   # Current date and time in string. 
now_tz=datetime.datetime.now(datetime.timezone.utc).astimezone().tzname() # Current timezone 

# HTML tables that will be send to xymon server. One table per monitored repo with the packages, the current version and the new one.
table="<h3>%s run at %s %s on %s</h3><br><br>" %(test, now, now_tz, bbmachine_name)

#####Functions

# Function to run when there has been a change (= when the 2 hashes are different or when the file containing the original hash does not exist). 
# Parameters :
#   hash_stdout : hash of the output of the shell command
#   blue_stdout : output of the xymondboard command to know if the test is currently blue
#   file_name : name of the file in which will be stored hash_stdout
def has_changed(hash_stdout,blue_stdout,file_name):
    # Create or overwrite a file storing hash_stdout
    file = open("%s/%s.txt"%(bbtmp, file_name), "w+") 
    file.write("%s"%hash_stdout)
    file.close()

    # If the test is blue, reactivate the test
    if (len(blue_stdout)!=0):
        reactivate=subprocess.Popen("%s %s 'enable %s.%s'"%(bbbin, bbdisp, bbmachine, test),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)


# Function to run the shell command.
# Parameter :
#   cmd : shell command to execute
# Return :
#   stdout : the stdout of the shell command if there are no mistakes without the first line
def stdout_cmd(cmd):
    # Get the output of the shell command cmd
    process = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate() 

    # If there is a problem then set the test color to red, send the test color and stderr to xymon server and exit the script
    if (process.returncode != 0):
        color="red"
        os.system("%s %s 'status %s.%s %s %s\n\n'" %(bbbin, bbdisp, bbmachine, test, color, stderr))
        sys.exit()

    # Delete the first line that prints "en train de lister ...
    stdout=re.sub('^.+\n', '', stdout)
    return(stdout)


# Function to run when stdout is empty
# Parameters :
#   blue_stdout : output of the xymondboard command to know if the test is currently blue
#   file_name : name of the file in which will be stored hash_stdout
def empty_stdout(file_name, blue_stdout,repo_list,i):
    global table

    # Put the path to the repository in the HTML table and that there are no update available 
    table += "<h4> Repository : %s , No update available </h4> " %(repo_list[i])
        
    # Define an empty hash    
    hash_stdout=''

    # If the file storing the hash does not exist OR it was blue or yellow before (=the file exist AND it is not empty) then call the has_changed function
    if (not os.path.exists("%s/%s.txt" %(bbtmp, file_name)) or ((os.path.exists("%s/%s.txt" %(bbtmp, file_name))) and (os.stat("%s/%s.txt"%(bbtmp, file_name)).st_size!=0))):
        has_changed(hash_stdout, blue_stdout, file_name)
    

# Function to run when stdout is not empty (= updates are available)
# Parameters :
#   blue_stdout : output of the xymondboard command to know if the test is currently blue
#   file_name : name of the file in which will be stored hash_stdout
#   stdout : the stdout of the shell command without the first line
def updates_available(stdout, file_name, blue_stdout):
    global has_changed_yellow, color

    # Hash stdout with md5
    hash_stdout=hashlib.md5(stdout.encode()).hexdigest() 

    # If a file containing the original hash of this repo exists 
    if (os.path.exists("%s/%s.txt" %(bbtmp, file_name))):
           
        # Get the original hash 
        file = open("%s/%s.txt"%(bbtmp,file_name), "r")
        hash_original = file.readline()    # There is only one line with the hash in the file
        file.close()

        # If the 2 hashes are different, it means that a new update is available
        if not (hash_stdout == hash_original):
            # There is a change so call has_changed function and set has_changed_yellow to True 
            has_changed(hash_stdout,blue_stdout,file_name)
            has_changed_yellow=True

    # If there are no file containing the original hash we consider that there have been a change
    else:
        # There is a change so call has_changed function and set has_changed_yellow to True 
        has_changed(hash_stdout,blue_stdout, file_name)
        has_changed_yellow=True

    # If the test is not blue or there have been a change in the hashes the test becomes yellow
    if (len(blue_stdout)==0 or has_changed_yellow):
        color = "yellow" 


# Function to run to fill the HTML table when updates are available and count the number of available updates
# Parameter :
#   stdout : the stdout of the shell command without the first line
#   repo_list : the list of the repositories monitored. It is the first parameter of the script. If no parameter is passed then repo_list=["all"]
#   i : index of repo_list. Identifies a repo in repo_list
# Return :
#   total_updates_for_one_repo : The number of updates available for ONE repo 
def fill_HTML_table(stdout, repo_list, i):
    global table

    # Get a list out of stdout output when it is not empty to fill the HTML table
    liste=stdout.split("\n")

    # Get the length of this list which is equal to the number of updates availables for THIS repo
    total_updates_for_one_repo=len(liste)  

    # Put the header rows in the HTML table : the first on states the repo and the number of updates available for this repo, the second the title of the 3 columns
    table += "<h4> Repository : %s , number of available update(s) : %s </h4> " %(repo_list[i], total_updates_for_one_repo)
    table += "<table border=1 cellpadding=10><tr> <th> Package </th> <th> Current version </th> <th> Newer version </th> </tr>" 

    # Put the list of updates available for this repo in the HTML table 
    for j in range(0, len(liste)):
        # Parse the line with a regex
        line_parsed=re.match("^(.+)?\/(.+)?\[[^:]*:\ (.+)?\]$",liste[j]) 
        # Fill the HTML table
        table +="<tr> <td>  %s  </td> <td> %s </td> <td> %s </td> </tr>" %(line_parsed.group(1), line_parsed.group(3), line_parsed.group(2))

    # Close the HTML table 
    table += "</table><br><br>"
    return(total_updates_for_one_repo)


###### Process the command line options
# Create a parser 
parser = argparse.ArgumentParser()

# Add an optional positional argument 
parser.add_argument("repositories",help="a list separated by comma of complete path to repo you want to monitor", nargs='?')

# Add an optional flag with a mandatory value
parser.add_argument("-r",help="alias of the host in hosts.cfg")

# Parse the argument 
arguments=parser.parse_args()

# If the optional flag r is initialized then change bbmachine_name, the name used to interrogate xymondboard
if arguments.r is not None:
    bbmachine_name=arguments.r
#    print(bbmachine_name)

# If there is an optional positional argument then initialize a list of repositories to monitor
if arguments.repositories is not None:
    repo_list=arguments.repositories.split(",")
    n=len(repo_list)   
    # Check if all the repositories exists and if not then exit the script 
    for i in range(0,n):
        if not os.path.exists(repo_list[i]):
                print("The repository {} does not exist".format(repo_list[i]))
                sys.exit(1)
#    print(repo_list)

######Script

# Check if the test is blue or if test is blue but without disabled status (meaning : not really "blue")
blue=subprocess.Popen("%s %s 'xymondboard host=%s test=%s' | head -n 1 | awk -F'\|' '{ print $3\",\"$9 }' | grep blue | grep -vE '^blue,0$'"%(bbbin, bbdisp, bbmachine_name, test),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)
blue_stdout = blue.communicate()[0] 

# If there are no parameter passed to the script
if (n==0):
    # Get the output of the cmd command
    cmd="apt list --upgradable"
    stdout=stdout_cmd(cmd)
    
    # Set the name of the file where you store the hash 
    file_name="all"
    
    # Set these 2 parameters just to have the following functions run correctly
    repo_list=["all"]
    i=0

    # If there are no update avalaible (If there is at least one update, there is a newline character)
    if (stdout.count('\n') ==0):
        empty_stdout(file_name, blue_stdout,repo_list,i) 

    # If updates are available
    else:
        
        # Delete the empty line(s) (the last one in particular)
        stdout=stdout.strip()  
        
        # Change the value of has_changed_yellow,fill the HTML table and get the total number of updates available
        updates_available(stdout, file_name, blue_stdout)
        total+=fill_HTML_table(stdout, repo_list, i) 


# If there is a parameter passed to the script (ie this script monitors specific(s) repo)
else:

    # Get the list of path(s) to a repository that we want to monitor from the parameter
    repo_list=sys.argv[1].split(",")

    # Process each element of repo_list (=each repo we want to monitor) 
    for i in range(0,len(repo_list)):

        # Get the string after the last slash. Useful to name the files differently  
        file_name=re.sub('^.*\/','', repo_list[i])

        # Get the output of the cmd command
        cmd="apt list -o Dir::Etc::SourceList=%s -o Dir::Etc::SourceParts=/dev/null --upgradable" %repo_list[i]
        stdout=stdout_cmd(cmd)

        # If there are no update avalaible (If there is at least one update, there is a newline character)
        if (stdout.count('\n') ==0):
            empty_stdout(file_name, blue_stdout, repo_list,i) 
            print("no updates available : has_changed_yellow is {}".format(has_changed_yellow))
        # If there are update available in this repository
        else:
            # Delete the empty line(s) (the last one in particular)
            stdout=stdout.strip()  
            
            # Change the value of has_changed_yellow,fill the HTML table and get the total number of updates available
            updates_available(stdout, file_name, blue_stdout)
            total +=fill_HTML_table(stdout, repo_list, i) # Fill the HTML table
 

#### Handle blue color 
# If the test is blue and there has not been a change between the 2 hashes then keep the test blue 
if (len(blue_stdout)!=0 and not has_changed_yellow):
    color="blue"

#DEBUG
#print(table)

#####Send to Xymon server
os.system("%s %s 'status %s.%s %s %s\n\n'" %(bbbin, bbdisp, bbmachine, test, color, table))
os.system("%s %s 'data %s.%s %s\n%s_total : %i\n\n'" %(bbbin, bbdisp, bbmachine, test, color, test, total))

