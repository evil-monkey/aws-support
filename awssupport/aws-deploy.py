#!/usr/bin/python

import sys
import getopt
import subprocess
import exceptions
import json
import logging

from aws.EcsSupport import EcsSupport

def print_help():
    print( """usage: aws-deploy.py [--help]
        [-c=cluster] [-s=service] [-t=tag] [-v|-vv|-vvv]

    Deploya una version especifica (tag) en un servicio de ECS. Busca la task definition
    asociada al servicio y crea una nueva revision de ser necesario. Luego actualiza el
    servicio.

    Parametros
    ==========

    -c, --cluster               Cluster: cluster en el que se encuentra el servicio 
				a deployar.

    -s, --service               Service: servicio que se actualizara.
 
    -t, --tag                   Tag del deployable. 
                                default: latest

    --v|--vv|--vvv                 Verbosidad
    
    """)
    return

def main(argv):

    tag = 'latest'
    cluster = ''
    service = ''
    log_level = logging.ERROR

    try:
        opts, args = getopt.getopt(argv,"hc:s:t:",["v","vv","vvv","help","cluster=","service=","tag="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h","--help"):
            print_help()
            sys.exit()
        elif opt in ("-t", "--tag"):
            tag = arg
        elif opt in ("-c", "--cluster"):
            cluster = arg
        elif opt in ("-s", "--service"):
            service = arg
        elif opt == "--vvv":
            log_level = logging.DEBUG
        elif opt == "--vv":
            log_level = logging.INFO
        elif opt == "--v":
            log_level = logging.WARN

    if cluster == '' or service == '':
        print ('\nERROR: cluster y service deben ser especificados.\n')
        print_help()
        sys.exit(2)

    if tag == 'latest':
        print ('\nWARN: Deployando version "latest"!\n')

    ecsSupport = EcsSupport(log_level)
    
    try:
        ecsSupport.deploy(cluster,service,tag)
    except ValueError as (msg):
        print "ERROR: %s" % msg
    except Exception as (msg):
        print "ERROR: {0}".format(msg)

if __name__ == "__main__":
   main(sys.argv[1:])
