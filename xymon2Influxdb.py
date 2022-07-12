#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import fileinput
import argparse
import pprint
import logging
import sys
import re
import os
import psutil
import socket
from signal import *
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import ConnectionError

pp = pprint.PrettyPrinter(indent=4)

class PrettyLog():

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return pprint.pformat(self.obj)
        self.obj = obj

def first_substring(strings, substring):
    try:
        return next(strings[i] for i, string in enumerate(strings) if substring in string)
    except StopIteration:
        return '--desc=Unkwown'

def is_number(s):
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False

    return True

def clean(*args):
    log.info("End of script.")
    sys.exit(0)

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, clean)

def main(influxserver='localhost', port=8086, user='admin', password='', dbname='xymon', doAllTest=True, test=[], xymonserver='neverland', extratag={}, metrics2Proccess=10):
    """
    ds0:ds1 1482514562:98572236333315:265177537713020 baco0016 if_load Po1
    ds0:ds1 1482514562:183165206223084:18364408483029 baco0016 if_load Fa0_1
    ds0:ds1 1482514562:18307594774107:183132742027739 baco0016 if_load Fa0_2
    varname[:varname:...]  epochtime:val[:val:...]  host  testname [tag]

    tag tiene el caracter ',' en lugar de '/'
    El numero de varname conincide con el numero de val que se suministra
    """
    test = list(set(test))               # remove duplicate elements
    # log.debug(PrettyLog(test))
    # test if I can connect to database and create my database in InfluxDB
    influx = ''
    try:
        influx = InfluxDBClient(influxserver, port, user, password, dbname)
        influx.create_database(dbname)
        log.info("new connection to {}".format(dbname))
    except InfluxDBClientError as e:
        log.warning(
            "Error while creating database, assuming it already exists:" + str(e[0]))
    except InfluxDBServerError as e:
        log.error("Error writting points " + str(e["error"]))
    except ConnectionError as e:
        log.error("Connection Error writting points " + str(e))
        quit()
    except Exception as e:
        log.error(
            "Error connecting with Influxdb server {}: {}".format(influxserver, str(e)))
        quit()
    metrics = list()
    for line in fileinput.input():       # loop forever...
        dataline = line.strip()
        datafields = dataline.split()
        if len(datafields) < 4:          # minimun 4 fields
            raise Exception("Malformed line, wrong fields number")
        client   = datafields[2]
        variable = datafields[0].split(':')
        value    = datafields[1].split(':')
        datatime = value.pop(0) # fist field from value is epoch time in seconds
        testname = datafields[3]
        log.debug("Parsed line: client %s, variable %s, value %s, datatime %s, testname %s", client, variable, value, datatime, testname) 
        # Should be same number of data an datanames
        if not variable or not value or len(variable) != len(value):
            log.warn(
                "Malformed line, data fields doesn't match value fields: {}".format(line))
            continue
        tag = datafields[4].replace(
            ',', '/').replace('=','\=') if len(datafields) >= 5 else ''  # tag is optional
        #Seems xymon split test by '_' (underscore) but we use ',' (comma).
        #This is a quick and dirty hack to fix it.
        if ',' in testname:
            splitField = testname.split(',',1)
            testname = splitField[0]
            tag = splitField[1].strip('.rrd').replace(',','/').replace('=','\=') + tag
            #log.warn("Ajuste requerido en lina '{}'. testname={} tag={}".format(line,testname, tag))
        if '.rrd' in testname:
            testname = testname.strip('.rrd')

        fieldsList = list()
        for key, val in zip(variable, value):
            if not val or val == 'U' or not is_number(val):
                continue
            fieldsList.append('{}={}'.format(key, val))
        if len(fieldsList) == 0:
            log.warn("No variable suitable for metrics: {}".format(line))
            continue
        fields = ','.join(fieldsList)

        if not doAllTest and testname not in test:
            log.debug("{} test not allowed".format(testname))
            continue

        # data channel don't split testname into testname and tag so we have to
        # do it here
        result = re.match("([^,]+)(,(.+))?\.rrd$", testname)
        if not tag and result and result.group(3):
            testname = result.group(1)
            tag = result.group(3).replace(',', '/')
            log.warn("Ajuste requerido en lina {}. testname={} tag={}".format(line,testname, tag))

        if result and result.group(1) and not result.group(3):
            log.warn("linea no contemplada {}. testname={} tag={}".format(line,testname, tag))
            continue
        tagsList = list()
        if client:
            tagsList.append('host={}'.format(client))
        if tag:
            tagsList.append('tag={}'.format(tag))
        if xymonserver:
            tagsList.append('server={}'.format(xymonserver))

        tags = ','.join(tagsList)

        # Important part
        line = '{},{} {} {}'.format(testname, tags, fields, datatime)
        metrics.append(line)

        # epoch to date
        hdate = datetime.fromtimestamp(
            int(datatime)).strftime('%Y-%m-%dT%H:%M:%SZ')

        log.debug("serie:{} date:{}".format(line, hdate))

        # Inlfuxdb thing
        if len(metrics) >= metrics2Proccess:
            size = sys.getsizeof(metrics)
            log.info("flush {} metrics list to InfluxDB ({} bytes)".format(len(metrics),size))
            try:
                influx.write_points(
                    metrics, time_precision='s', protocol='line')
                #log.debug("Writed")
                metrics = list()
            except InfluxDBClientError as e:
                log.error("Client Error writting points " + str(e))
                log.warning(PrettyLog(metrics))
                metrics = list()  # discard bad metrics
            except InfluxDBServerError as e:
                log.error("Error writting points " + str(e))
                metrics = list()
#                influx = InfluxDBClient(host, port, user, password, dbname)
            except ValueError as e:
                log.error("Value Error writting points " + str(e))
            except ConnectionError as e:
                log.error("Connection Error writting points " + str(e))
                influx = InfluxDBClient(
                    influxserver, port, user, password, dbname)  # Reconnect
            except Exception as e:
                log.error("Unkwown Error writting points " + str(e))
    if len(metrics) > 0:
        try:
            # Last thing to do si flush data to influxdb
            size = sys.getsizeof(metrics)
            log.info("flush {} metrics list to InfluxDB ({} bytes)".format(len(metrics),size))
            influx.write_points(metrics, time_precision='s', protocol='line')
        except Exception as e:
            log.error("Ending but an unkwown error was raised " + str(e))
            log.error(PrettyLog(metrics))

def getConfig(hostname, desc):
    completeDetails = {
        hostname: {
            'influxserver': '192.168.15.43',
            'port': 8086,
            'user': 'xymon',
            'password': 'tr1p4x',
            'dbname': 'xymon',
            'logfile': '/var/log/xymon/xymon2Influxdb.log',
            'metrics2Proccess': 10,
            'test': [],
            'extratag': [],
            'verbose': True
        }
    }
    
    if desc in completeDetails[hostname] and 'logfile' in completeDetails[hostname][desc]:
        completeDetails[hostname]['logfile'] = completeDetails[hostname][desc]['logfile']
    #print(PrettyLog(completeDetails))
    return completeDetails

if __name__ == '__main__':
    hostname = socket.gethostname().split('.')[0]
    
    sys.argv = []    # needed to fileinput.input don't mess up with argv
    #find type of process in pparent process xymond_rrd
    parentPid = os.getppid()
    process_name = psutil.Process(parentPid).cmdline()
    desc  = first_substring(process_name, 'desc').split('=')[-1]
    config = getConfig(hostname, desc)
    try:
        if config[hostname]['verbose']:
            logging.basicConfig(filename=config[hostname]['logfile'], level=logging.DEBUG,
                                format='%(asctime)s %(name)-23s (%(process)-4d) %(levelname)-7s- [{}] %(message)s'.format(desc))
        else:
            logging.basicConfig(filename=config[hostname]['logfile'], level=logging.INFO,
                                format='%(asctime)s %(name)-23s (%(process)-4d) %(levelname)-7s- [{}] %(message)s'.format(desc))
    except Exception as e: 
        print('can\'t write in log file {}: {}'.format(config[hostname]['logfile'], str(e)))
    # logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    log = logging.getLogger('xymon2Influxdb')
    log.debug("influx host: {}".format(config[hostname]['influxserver']))

#    extratag = dict()
#    if args.extratag:
#        extratag = dict(item.split("=") for item in args.extratag.split(",")) 
    main(influxserver = config[hostname]['influxserver'], port = config[hostname]['port'], user = config[hostname]['user'], xymonserver = hostname,
         password = config[hostname]['password'], dbname = config[hostname]['dbname'], test = config[hostname]['test'], extratag = config[hostname]['extratag'],
         metrics2Proccess = config[hostname]['metrics2Proccess'])
 
    log.info("End of script.")
