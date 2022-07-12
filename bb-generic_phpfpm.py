#!/usr/bin/env python3

#### Meta information
# Translation of a perl script by ZeWaren to a python script by Aurelia Bordes (sys.vision)  

#### Modules
import os 
import sys
import getopt
import re
from urllib.error import URLError, HTTPError
from urllib.request import urlopen
import datetime

#### Variables
test="php-fpm"
color="red"
PHP_FPM_STATUS_PAGE=''
XYMON_WWW_ROOT=''
content={}
date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
now_tz=datetime.datetime.now(datetime.timezone.utc).astimezone().tzname()

#### Environment variables
bb=os.environ['BB']
bbdisp=os.environ['BBDISP']
bbmachine=os.environ['MACHINE']
bbmachinedots=os.environ['MACHINEDOTS']

#### Function
def get_graph_html(host, service):
    return ('<table summary="'+service+' Graph"><tr><td><A HREF="'+XYMON_WWW_ROOT+'/xymon-cgi/showgraph.sh?host='+host+'&amp;service='+service+'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='+host+'&amp;action=menu"><IMG BORDER=0 SRC="'+XYMON_WWW_ROOT+'/xymon-cgi/showgraph.sh?host='+host+'&amp;service='+service+'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='+host+'&amp;graph=hourly&amp;action=view" ALT="xymongraph '+service+'"></A></td><td align="left" valign="top"></td></tr></table>')

# Return the help function
def doc():
	print(
"""Usage: {} [-h] -u [url]

        Required parameters:

        -u [url]   	URL of the php-fpm status page            

        Optional parameters:

        -h			Display this help message and exit.
""".format(sys.argv[0]))


##### Process comand line argument

arguments=sys.argv[1:]  # The first one is the name of the script

# The getopt.getopt function returns a list of tuples(flag,value) and the list of remaining arguments after all the options have been parsed out.
try :
    opts,args=getopt.getopt(arguments,"hu:")

# when an unrecognized option is found in the argument list or when an option requiring an argument is given none.
except getopt.GetoptError:
    doc()
    print ("Invalid argument")
    sys.exit(2)

for opt,arg in opts:
    if opt =='-h':
        doc()
        sys.exit(0)
    elif (opt =='-u' and not bool(re.match("http[s]?://(.*)", arg))):
        doc()
        print("Invalid URL parameter")
        sys.exit(1)
    elif (opt =='-u'):
        PHP_FPM_STATUS_PAGE=arg
    else:
        doc()
        print("you need to pass the URL of the php-fpm status page")
        sys.exit(1)


##### Script

try:
    page=urlopen(PHP_FPM_STATUS_PAGE)
except URLError as e:
    print("URL cannot be opened : {}".format(e.reason))
    sys.exit(1)

page_bytes=page.read()
page_string=page_bytes.decode("utf-8")
page_string=page_string.strip()   # Remove the last \n

lines=page_string.split("\n") # Create a list out of page_string

for i in range(0,len(lines)):
    lines_split=lines[i].split(":") # Split each line around :, the first element will be the key and the second the value
    try:
        lines_split[1]=lines_split[1].lstrip()  # Remove leading whitespaces on the 2nd element
    except:
        print("URL status with gargage")
        sys.exit(1)
    content[lines_split[0]]=lines_split[1]  # Fill the dictionnary

# If the match fails 
if (content=={}):
    trends="" # No trend message
    status="Error !" # Print Error on the page dedicated to nginx_py

# If the match suceeds
else:
    color="clear" # Change the color to clear (=no test)

    # Fill the "trend" message (see Xymon docs)
    # Be VERY CAREFUL about \n. If there are no newline before the name of the RRD file it is not created !!
    # Don't forget to put a space between the "DS" part of the line and the variable because it won't work otherwise
    trends = "\n[phpfpm_py_connections.rrd]\nDS:acceptedconn:DERIVE:600:0:U "+content['accepted conn']+"\n[phpfpm_py_processes.rrd]\nDS:idle:GAUGE:600:0:U "+content['idle processes']+"\nDS:active:GAUGE:600:0:U "+content['active processes']+"\nDS:total:GAUGE:600:0:U "+content['total processes']

    # status is what will be shown on the xymon front end (the column phpfpm_py) 
status = "<h2>Status</h2> URL: {} <br><br>  No status checked  <h2> Counters</h2>".format(PHP_FPM_STATUS_PAGE)+get_graph_html(bbmachinedots, 'phpfpm_py_connections')+get_graph_html(bbmachinedots, 'phpfpm_py_processes')

# DEBUG
#print(trends)
#print(status)

##### Send to xymon server
os.system("%s %s 'status %s.%s %s %s %s %s\n\n'" %(bb, bbdisp, bbmachine, test, color, date, now_tz, status))

# If the trends string is not empty (=we succeeded in getting data from the webpage) then send it to data channel
if (trends):
    os.system("%s %s 'data %s.trends %s\n\n'" %(bb, bbdisp, bbmachine, trends))
