#!/usr/bin/env python3

#### Meta information
# OS : Linux (Debian-like), FreeBSD
# Author : Aurelia Bordes (sys.vision)

#### Module
import os

##### Environment variables
bb=os.environ['BB']
bbdisp=os.environ['BBDISP']
machine=os.environ['MACHINE']

##### Variable
test = "processors"

##### Script
nb_cpu=os.cpu_count()

# DEBUG
#print(nb_cpu)

##### Send to Xymon server
os.system("%s %s 'data %s.%s\n%s : %s\n'" %(bb, bbdisp, machine, test, test, nb_cpu) )
