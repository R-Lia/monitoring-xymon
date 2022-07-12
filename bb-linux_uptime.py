#!/usr/bin/env python3 

#### Meta information
# Written for Ubuntu
# Xymon script
# Author : Aurelia Bordes

#### Goal
# Send to xymon server the uptime of the client

#### Module
import os

#### Environment variables
bb=os.environ['BB']
bbdisp=os.environ['BBDISP']
machine=os.environ['MACHINE']

#### Variable to set up
test="uptime"

#### Script
with open('/proc/uptime', 'r') as f:
	uptime_seconds = float(f.readline().split()[0])

#### Send to Xymon server
os.system("%s %s 'data %s.%s\n%s : %.5f\n'" %(bb, bbdisp, machine, test, test, uptime_seconds))
