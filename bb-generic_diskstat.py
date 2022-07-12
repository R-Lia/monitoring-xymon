#!/usr/bin/env python3

#### Meta information
# Xymon script
# Author : Aurelia Bordes (sys.vision)

###### Modules
import subprocess
import csv
import os

###### Variables
test="diskstat"

##### Function 
def cmd_preprocess(cmd):
    # Execute the shell command and capture its output 
    process = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT, universal_newlines=True)
    stdout = process.communicate()[0] # Capture stdout

    # Create a list out of stdout 
    format=str(stdout).split("\n")

    # DEBUG
    # print("FORMAT", format, "FORMAT_END")

    # Parse the file
    reader = csv.DictReader(format, delimiter='|') 
    return(reader)


###### Script
# Get the OS 
os_info = os.uname()[0] 

# If the OS is Linux 
if (os_info=="Linux"):
    cmd="iostat -xdkz | grep -v '^$' | sed -ne '2,/^device/{p;}' | egrep -i '^(device|hd|sd|vd|nvme)' | sed -r 's/[[:blank:]]+/|/g'"
    reader=cmd_preprocess(cmd)
    for row in reader:
        rs=row['r/s'].replace(",",".")
        ws=row['w/s'].replace(",",".")
        krs=row['rkB/s'].replace(",",".")
        kws=row['wkB/s'].replace(",",".")
        r_await=row['r_await'].replace(",",".")
        w_await=row['w_await'].replace(",",".")


# If the OS is FreeBSD
elif (os_info=="FreeBSD"):
    cmd = "iostat -dxt da | grep -v '^$' | sed -ne '2,/^device/{p;}' | sed -r 's/[[:blank:]]+/|/g'|sed 's/\|$//'"
    reader=cmd_preprocess(cmd)
    for row in reader:
        rs=row['r/s'].replace(",",".")
        ws=row['w/s'].replace(",",".")
        krs=row['kr/s'].replace(",",".")
        kws=row['kw/s'].replace(",",".")
        r_await=row['ms/r'].replace(",",".")
        w_await=row['ms/w'].replace(",",".")


##### Send to xymon server
os.system("%s %s 'data %s.%s\n%s_rs : %s\n%s_ws : %s\n%s_krs : %s\n%s_kws : %s\n%s_rawait : %s\n%s_wawait : %s\n'" %(os.environ['BB'], os.environ['BBDISP'], os.environ['MACHINE'], test, test, rs, test, ws, test, krs, test, kws, test, r_await, test, w_await))
