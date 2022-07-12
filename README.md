# OVERVIEW 
## INTRODUCTION

This repository contains a list of Xymon script written in shell, python and perl. Some scripts are compatible with FreeBSD, others with Linux (Debian-like) but the majority of them are compatible with both. These scripts are designed to run on the client side of the Xymon monitoring tool. 

Each of these script monitors a specific item on the client host and sends metrics and/or a status to the xymon server. In the "scripts description" section, a more detailed view of what each script does will be given.

## TECHNOLOGIES
Languages : 
* plain shell (without bashisms)
* python3
* perl5

OS : 
* FreeBSD
* Linux (Debian-like)

Dependencies :  
* DBI module (for bb-generic_mysql.pl) 
* DBD:mysql module (for bb-generic_mysql.pl)
* Unix:Uptime module (for bb-generic_uptime.pl)

## FreeBSD and python scripts
For portability, we use "/usr/bin/env python3" in the shebang at the beginning of the scripts. However on Linux there is a shortcut "python3" that does not exist on FreeBSD (you have to specify the version python like python3.7). As such, on FreeBSD, you can install the meta-port python3 at https://www.freshports.org/lang/python3/ that will create a link /usr/local/bin/python3.

To get the env command working, you have to add the path to PATH in xymonclient.cfg :  
`PATH="..:/usr/local/bin:/usr/local/sbin:" `

## Using a SSH tunnel
In $XYMONCLIENTHOME/etc/xymonclient.cfg 
* If you use bb-generic_ssh_tunnel.sh leave XYMSRV=127.0.0.1
* If you do not use bb-generic_ssh_tunnel.sh set XYMSRV to the IP address of your xymon server

# SCRIPTS DESCRIPTION

## FREEBSD SCRIPTS
     

### bb-freebsd_audit.sh

Goal :       

* Send to Xymon data channel the number of problem(s) and the number of package(s) with problem(s) detected by the command "pkg audit"  
* Send to Xymon status channel the test color and the output of the "pkg audit" command  

When disabled manually, the test will remain blue until a change is detected. This change is detected by asking xymon server via xymondboard.  

Parameter :
* -r [hostname] : alias (if any) created in the hosts.cfg file. Used to interrogate xymondboard (optional)

Graph method : NCV method 

Create a column on xymon webpage : yes


### bb-freebsd_jails.sh
Goal :  
* Send to Xymon data channel the number of subjails running on the host

Type of server : Run on host master and master jail

Graph method : None

Create a column on xymon webpage : no


### bb-freebsd_raid.sh
Goal :  
* Send to Xymon status channel the test color and mpt raid controller(s) information and their status via the sysctl command

Type of server : Run on host master

Graph method : None 

Create a column on xymon webpage : yes


### bb-freebsd_zfs.sh
Goal :  
* Send to Xymon data channel a trends message with zfs pool(s) and their capacity
* Send to Xymon status channel the test color and a table with info about the zpools and a table with the list of snapshots

Parameters :
* -diskyell [number] : Percentage of capacity from which the CAP_COLOR becomes yellow (optional)
* -diskred [number] : Percentage of capacity from which the CAP_COLOR becomes red. (optional) 
* -snapyell [number] : Number of days from which the LINE_COLOR becomes yellow. (optional)
* -snapred [number] : Number of days from which the LINE_COLOR becomes red. (optional)
* -snapcol [bool] : Say if the snapshot age should affect the test color (LINE_COLOR). (optional)
* -checksnaps [bool] : Say if snapshots are checked. (optional)
* -h : help and exit. (optional)

Type of server : Run on host master and master jail

Graph method : trends message 

Create a column on xymon webpage : yes



## LINUX-DEBIAN SCRIPTS

### bb-linux_debian_apt_check.py
Goal :  
* Send to Xymon data channel the test color and the total number of updates available for either specific repositories (chosen by you and passed as a parameter to the script) or by default (when no parameter is passed to the script) for the output of "apt list --upgradable"   
* Send to Xymon status channel the test color and a HTML table filled with the list of updates available defined as above  

When disabled manually, the test will remain blue until a change is detected. This change is detected by asking xymon server via xymondboard.  

Parameters :
* category : a list separated by comma of complete paths to a specific repository (optional) 
* -r [hostname] : alias (if any) created in the hosts.cfg file. Used to interrogate xymondboard (optional)
* -h : help and exit (optional)

Examples:
* b-linux_debian_apt_check.py /etc/apt/sources.list.d/ondrej-ubuntu-php-bionic.list,/etc/apt/sources.list.d/teamviewer.list -r Eowind
* b-linux_debian_apt_check.py -r Eowind /etc/apt/sources.list.d/ondrej-ubuntu-php-bionic.list,/etc/apt/sources.list.d/teamviewer.list 

Graph method : NCV method  

Create a column on xymon webpage : yes


### bb-linux_debian_apt_history.py
Goal :  
* Send to Xymon data channel the total number of updated packages, the total number of removed packages and the total number of installed packagesfor the last x days (to define) found in the /var/log/dpkg.log file.  
* Send to Xymon status channel the test color and 3 HTML tables each filled with either the list of updated, removed or installed packages defined as above    

When disabled manually, the test will remain blue until a change is detected. This change is detected by asking xymon server via xymondboard.  

Parameters :
* repository : a list separated by comma of the categories of packages you want to monitor (upgrade,remove,install) (optional) 
* -r [hostname] : alias (if any) created in the hosts.cfg file. Used to interrogate xymondboard (optional)
* -h : help and exit (optional)

Examples:
* bb-linux_debian_apt_history.py upgrade,install -r Eowind
* bb-linux_debian_apt_history.py -r Eowind upgrade,install,remove

Graph method : NCV method   

Create a column on xymon webpage : yes


### bb-linux_uptime.py
Goal :  
* Send to Xymon data channel the uptime in seconds of the OS by reading it from "/proc/uptime". 

Graph method : None   

Create a column on xymon webpage : no



## GENERIC SCRIPTS

### bb-generic_diskstat.py
Goal :  
* Send to Xymon data channel 6 metrics extracted from the output of iostat command.

Graph method : NCV method 

Create a column on xymon webpage : no


### bb-generic_mysql.pl
Goal :  
* Send to Xymon data channel a trends message with metrics extracted from the performance_schema vue of the mysql server
* Send to Xymon status channel the test color and 12 graphs

Parameters :
* -u [username] : username on mysql server (mandatory)
* -p [password] : password corresponding to the username (mandatory)
* -h : help and exit (optional)

Dependencies :
* DBI module : libdbi-perl for Debian-like
* DBD:mysql module : libdbd-mysql-perl for Debian-like

Graph method : trends message

Create a column on xymon webpage : yes


### bb-generic_nginx.py
Goal :
* Send to Xymon data channel a trends message with metrics extracted from the nginx status page
* Send to Xymon status channel the test color and 2 graphs 

Parameters :
* -u [url] : URL of the Nginx status page (mandatory)
* -h : help and exit (optional)

Graph method : trends message

Create a column on xymon webpage : yes


### bb-generic_phpfpm.py
Goal :
* Send to Xymon data channel a trends message with metrics extracted from the php fpm status page
* Send to Xymon status channel the test color and 2 graphs

Parameters :
* -u [url] : URL of the phpfpm status page (mandatory)
* -h : help and exit (optional)

Graph method : trends message

Create a column on xymon webpage : yes


### bb-generic_process.sh
Goal :
* Send to Xymon data channel the total number of processes by category (process in disk wait, idle process, process waiting to acquire a lock, runnable process, process sleeping for less than 20sec, stopped process, idle interrupted threads, zombie process)

Graph method : NCV method 

Create a column on xymon webpage : no


### bb-generic_processors.py
Goal :
* Send to Xymon data channel the number of CPU 

Type of server : Run on host master

Graph method : NCV method 

Create a column on xymon webpage : no


### bb-generic_ssh-tunnel.sh
Goal :
* Send to Xymon status channel the test color.   
Set up a SSH tunnel between the client and xymon-server. If there is more than one SSH tunnel, the script kills all of them and restarts one.  

Parameters :
* -r [hostname or IP address] : IP address or hostname of xymon server (mandatory)
* -p [port number] : Port (optional)
* -i [absolute path] : Path to the file containing the private key of the host (optional) 
* -h : help and exit (optional)

Type of server : xymon clients that are not on the same machine as xymon server 

Graph method : None 

Create a column on xymon webpage : yes


### bb-generic_storage.sh
Goal :
* Send to Xymon data channel the total number of bytes available for storage, the number of already allocated bytes to storage and the number of free bytes for storage (storage = storage_alloc + storage_free)

Type of server : Run on host master

Graph method : None 

Create a column on xymon webpage : no



### bb-generic_time_diff.sh
Goal :
* Send to Xymon status channel the test color and the time offset of the host given by the "ntpdate" command with a configurable NTP server

Graph method : NCV method 

Create a column on xymon webpage : yes


### bb-generic_uptime.pl
Goal :  
* Send to Xymon data channel the uptime in seconds of the OS 

Dependencies :
* Unix:uptime module 

Graph method : None

Create a column on xymon webpage : no


## Summary table

| Scripts | OS | Dependencies | Type of server | Parameters | Graph method | status column | Interrogate xymondboard | Script customization needed |
| ------- | --- | ----------- | -------------- | ---------- | ------------ | --------------- | ----------------------- | ------- |
| bb-freebsd_audit.sh | FreeBSD | No | All | No | NCV | Yes | Yes | No |
| bb-freebsd_jails.sh | FreeBSD | No | host master and master jail | No | None | No | No | No |
| bb-freebsd_raid.sh | FreeBSD | No | host master with mpt raid controller| No | None | Yes | No | No |
| bb-freebsd_zfs.sh | FreeBSD | No | host master and master jail | optional | trends | Yes | No | No |
| bb-linux_debian_apt_check.py | Linux (Debian-like) | No | All | optional | NCV | Yes | Yes | No |
| bb-linux_debian_apt_history.py | Linux (Debian-like) | No | All | optional | NCV | Yes | Yes | No |
| bb-linux_uptime.py | Linux | No | All | No | None | No | No | No |
| bb-generic_diskstat.py | FreeBSD + Linux | No | All | No | None | No | No | No |
| bb-generic_mysql.pl | FreeBSD + Linux | Yes (2) | MySQL Server | Yes | trends | Yes | No | Yes |
| bb-generic_nginx.py | FreeBSD + Linux | No | Nginx Server | Yes | trends | Yes | No | Yes |
| bb-generic_phpfpm.py | FreeBSD + Linux | No | webserver server with php-fpm | Yes | trends | Yes | No | Yes |
| bb-generic_process.sh | FreeBSD + Linux | No | All | No | NCV | No | No |  No |
| bb-generic_processors.py | FreeBSD + Linux | No | host master | No | NCV | No | No |  No |
| bb-generic_ssh_tunnel.sh | FreeBSD + Linux | No | Client not on xymon server | Yes | None | Yes | No | No |
| bb-generic_storage.sh | FreeBSD + Linux | No | host master | No | None | No | No | No |
| bb-generic_time_diff.sh | FreeBSD + Linux | No | All | No | NCV | Yes | No | No |
| bb-generic_uptime.pl | FreeBSD + Linux | Yes (1) | All | No | NCV | No | No | No |


# INSTALLATION

## INTRODUCTION
The installation of a xymon custom script and the setup of its graph is detailed in the official manpage of xymon : https://www.xymon.com/help/howtograph.html

As we can see, there are 2 ways of setting up graphs. **Most of these scripts use the NCV method**. As a consequence the installation of these scripts is almost always the same. Below is a generic procedure of installation. Then, there is a full example of the installation of bb-generic_apt_history.py. Be aware that some scripts recquire other little steps to be correctly configure. These extra steps will be written at the top of the script.

The configuration files for these scripts can be found in the repositories monitoring/xymon-conf-client and monitoring/xymon-conf-server.

## GENERIC PROCEDURE OF INSTALLATION
### CONFIGURATION ON THE CLIENT SIDE 
1. Copy the scripts you want somewhere executable by your xymon client (typically $XYMONCLIENTHOME/ext).  
2. Set the permissions accordingly (typically chmod +x).  
3. Add the corresponding task in $XYMONCLIENTHOME/etc/clientlaunch.cfg (see the corresponding conf file in the repo monitoring/xymon-conf-client).  

### CONFIGURATION ON THE SERVER SIDE
If you use the NCV or SPLITNCV method, add the name_of_the_test=ncv to TEST2RRD in $XYMONHOME/etc/xymonserver.cfg  
If you use the NCV or SPLITNCV method, add  NCV_name_of_the_test="dataset1:datatype,dataset2:datatype"in $XYMONHOME/etc/xymonserver.cfg  
If you want the graph(s) to appear in the trends column, add the name of the rrd file to GRAPHS in $XYMONHOME/etc/symonserver.cfg  
If you want a graph to appear at all, add the corresponding graph definition to $XYMONHOME/etc/graphs.cfg (see the corresponding conf file in the repo monitoring/xymon-conf-server)  


## FULL EXAMPLE : INSTALLATION OF bb-generic_apt_history.py
This script follows the classic procedure of setting a custom graph (cf The NCV and SPLITNCV methods https://www.xymon.com/help/howtograph.html).  

In this example, we consider that we want the graph to appear in the trends column.

### CONFIGURATION ON THE CLIENT SIDE
1. Copy bb-generic_apt_history.py to $XIMONCLIENTHOME/ext/

2. `chmod +x bb-generic_apt_history.py`

3. Add in $XYMONCLIENTHOME/etc/clientlaunch.cfg :

```
[apt_history]  
    ENVFILE $XYMONCLIENTHOME/etc/xymonclient.cfg
    CMD $XYMONCLIENTHOME/ext/bb-generic_apt_history.py
    LOGFILE $XYMONCLIENTLOGS/bb-generic_apt_history.log
    INTERVAL 1m
```
 
This configuration can be found in the repository monitoring/xymon-conf-client


### CONFIGURATION ON THE SERVER SIDE
Add to TEST2RRD to generate a RRD file:  
`TEST2RRD="...,apt_history=ncv"`

Below GRAPHS, add an extra settings to tell Xymon to create a RRD file with 3 datasets of datatype GAUGE:  
`NCV_apt_history="apthistoryinstall:GAUGE,apthistoryremove:GAUGE,apthistoryupgrade:GAUGE"`

As we want the graph to appear in the trends column as well add to GRAPHS :  
`GRAPHS="...,apt_history"`

Add in $XYMONHOME/etc/graphs.cfg :  
```
[apt_history]
        FNPATTERN ^apt_history.rrd
        TITLE Apt packages changes / period
        YAXIS Packages count
        DEF:install@RRDIDX@=@RRDFN@:apthistoryinstall:AVERAGE
        DEF:remove@RRDIDX@=@RRDFN@:apthistoryremove:AVERAGE
        DEF:upgrade@RRDIDX@=@RRDFN@:apthistoryupgrade:AVERAGE
        LINE1:install@RRDIDX@#00FF00:@RRDMETA@ Installed
        GPRINT:install@RRDIDX@:LAST: %6.1lf (cur) \:
        GPRINT:install@RRDIDX@:MAX: %6.1lf (max) \:
        GPRINT:install@RRDIDX@:MIN: %6.1lf (min) \:
        GPRINT:install@RRDIDX@:AVERAGE: %6.1lf (avg)\n
        LINE1:remove@RRDIDX@#0000FF:@RRDMETA@ Removed
        GPRINT:remove@RRDIDX@:LAST: %6.1lf (cur) \:
        GPRINT:remove@RRDIDX@:MAX: %6.1lf (max) \:
        GPRINT:remove@RRDIDX@:MIN: %6.1lf (min) \:
        GPRINT:remove@RRDIDX@:AVERAGE: %6.1lf (avg)\n
        LINE1:upgrade@RRDIDX@#FF0000:@RRDMETA@ Upgraded
        GPRINT:upgrade@RRDIDX@:LAST: %6.1lf (cur) \:
        GPRINT:upgrade@RRDIDX@:MAX: %6.1lf (max) \:
        GPRINT:upgrade@RRDIDX@:MIN: %6.1lf (min) \:
        GPRINT:upgrade@RRDIDX@:AVERAGE: %6.1lf (avg)\n`
```

## SCRIPTS WITH EXTRA INSTALLATION STEPS


# TROUBLESHOOTING

Note that in the extra setting NCV_name_of_the_test="dataset1:datatype1,dataset2:datatype2", you MUST NOT write the underscores or any special characters in the name of the metric. Otherwise, it won't be taken into account when the RRD file is created and the dataset will be of type DERIVE regardless of what you wrote.


# INSPIRATION AND CREDITS
bb-freebsd_raid.sh is the shell version of a script by Nicolas Liénard   
bb-freebsd_zfs.sh is the shell version of a script by Vernon Everett : https://wiki.xymonton.org/doku.php/monitors:bb-zfs  
bb-generic_phpfpm.py is the python version of a script by ZeWaren : https://github.com/ZeWaren/xymon-php-fpm  
bb-generic_nginx.py is the python version of a script by ZeWaren : https://github.com/ZeWaren/xymon-nginx   
bb-generic_mysql.pl is modified version (information_schema is switched to performance_schema) of a script by ZeWaren : https://github.com/ZeWaren/xymon-mysql-counters  
bb-generic_ssh_tunnel.sh is a modified version of a script by Padraig Lennon : https://wiki.xymonton.org/doku.php/addons:ssh_tunnel  


