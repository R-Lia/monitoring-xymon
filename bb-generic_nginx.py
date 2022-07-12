#!/usr/bin/env python3

#### Meta information
# Translation of a perl script by ZeWaren to a python script by Aurelia Bordes(sys.vision)

##### Modules
import re
import os
import sys
import getopt
import datetime
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

##### Variables
test="nginx_py"
color="red"
nginx_status=""     # URL of the Nginx status page. Should be initiated via an argument passed to this script
date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
now_tz=datetime.datetime.now(datetime.timezone.utc).astimezone().tzname() # Current timezone
XYMON_WWW_ROOT=""

##### Environment variables
bb=os.environ['BB']
bbdisp=os.environ['BBDISP']
bbmachine=os.environ['MACHINEDOTS']

##### Functions
# Return the graphs that will be printed on the column nginx_py
def get_graph_html(host,service):
    return('<table summary="'+service+' Graph"><tr><td><A HREF="'+XYMON_WWW_ROOT+'/xymon-cgi/showgraph.sh?host='+host+'&amp;service='+service+'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='+host+'&amp;action=menu"><IMG BORDER=0 SRC="'+XYMON_WWW_ROOT+'/xymon-cgi/showgraph.sh?host='+host+'&amp;service='+service+'&amp;graph_width=576&amp;graph_height=120&amp;first=1&amp;count=1&amp;disp='+host+'&amp;graph=hourly&amp;action=view" ALT="xymongraph '+service+'"></A></td></tr></table>')

# Return the help function
def doc():
	print(
"""Usage: {} [-h] -u [url]

        Required parameters:

        -u [url]   	URL of the Nginx status page            

        Optional parameters:

        -h			Display this help message and exit.
""".format(sys.argv[0]))


##### Process comand line argument

arguments=sys.argv[1:]  # The first one is the name of the script

# Return a list of tuples, followed by the list of remaining arguments after all the options have been parsed out.
try :
    opts,args=getopt.getopt(arguments,"hu:")

# when an unrecognized option is found in the argument list or when an option requiring an argument is given none.
except getopt.GetoptError:
    doc()
    print ("Invalid argument")
    sys.exit(2)

for opt,arg in opts:
    if (opt =='-u' and not bool(re.match("http[s]?://.*",arg))):
        doc()
        print("Invalid URL parameter")
        sys.exit(1)
    elif (opt =='-u'):
        nginx_status=arg
    elif opt =='-h':
        doc()
        sys.exit(1)
    else:
        doc()
        print("you need to pass the URL of the nginx status page")
        sys.exit()


##### Script

# Preprocess the webpage nginx status to use regex on it
try:
    page = urlopen(nginx_status) #HTTPResponse object
except URLError as e:
    print("URL cannot be opened : {}".format(e.reason))
    sys.exit(1)

page_bytes=page.read() # The content of the nginx status web page in bytes object
page_string=page_bytes.decode("utf-8") # The content of the nginx status web page in string

# Regex to match the info that interest us and put it into variables.
content=re.match(r"Active connections: (?P<active>\d+) \nserver accepts handled requests\n (?P<accepted_connections>\d+) (?P<handled_connections>\d+) (?P<handled_requests>\d+) \nReading: (?P<reading>\d+) Writing: (?P<writing>\d+) Waiting: (?P<waiting>\d+)", page_string)

# If the match fails 
if (content==None):
    trends="" # No trend message
    status="Error !" # Print Error on the page dedicated to nginx_py
    
# If the match suceeds
else:
    color="clear" # Change the color to clear (=no test)
    content=content.groupdict() # Put the retrieved data in a dictionnary. Useful because it is easier to access it.

    # Fill the "trend" message (see Xymon docs)
    # Be VERY CAREFUL about \n. If there are no newline before the name of the RRD file it is not created !!
    # Don't forget to put a space between the "DS" part of the line and the variable because it won't work otherwise
    trends = "\n[nginx_py_connections.rrd]\nDS:total:GAUGE:600:0:U "+content['active']+"\nDS:reading:GAUGE:600:0:U "+content['reading']+"\nDS:writing:GAUGE:600:0:U "+content['writing']+"\nDS:waiting:GAUGE:600:0:U "+content['waiting']+"\n[nginx_py_requests.rrd]\nDS:accepted:DERIVE:600:0:U "+content['accepted_connections']+"\nDS:handconn:DERIVE:600:0:U "+content['handled_connections']+"\nDS:handreq:DERIVE:600:0:U "+content['handled_requests']

    # data is what will be shown on the xymon front end (the column nginx_py) 
    status = "<h2>Status</h2> URL : {} <br><br> No status checked  <h2> Counters</h2>".format(nginx_status)+get_graph_html(bbmachine, 'nginx_py_connections')+get_graph_html(bbmachine, 'nginx_py_requests')

# DEBUG
print("trends : ", trends)
print(status)

##### Send to xymon server
os.system("%s %s 'status %s.%s %s %s %s\n\n'" %(bb, bbdisp, bbmachine, test, color, date, status))

# If the trends string is not empty (=we succeeded in getting data from the webpage) then send it to data channel
if (trends):
    os.system("%s %s 'data %s.trends %s\n\n'" %(bb, bbdisp, bbmachine, trends))
