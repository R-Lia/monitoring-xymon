#!/usr/bin/env perl

#### Meta information
# OS : Linux, FreeBSD
# Author : Aurelia Bordes (sys.vision)

use warnings;

#### Module
use Unix::Uptime;

#### Variable
my $test = "uptime";

#### Script
my $uptime = Unix::Uptime->uptime();

#DEBUG
#print $uptime;

#### Send to xymon server 
system( "$ENV{BB} $ENV{BBDISP} 'data $ENV{MACHINEDOTS}.$test\n $test : $uptime\n'");
