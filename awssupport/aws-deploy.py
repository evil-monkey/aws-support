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
        [-c=cluster] [-s=service] [-t=tag] [-v|-vv|-vvv] [-d=dryrun]

    Deploya una version especifica (tag) en un servicio de ECS. Busca la task definition
    asociada al servicio y crea una nueva revision de ser necesario. Luego actualiza el
    servicio.

    Parametros
    ==========

    -h, --help                  Ayuda: esta ayuda!

    -c, --cluster               Cluster: cluster en el que se encuentra el servicio 
				a deployar.

    -s, --service               Service: servicio que se actualizara.
 
    -n, --container             Container: nombre del container dentro de 
                                la task definition.
 
    -t, --tag                   Tag del deployable. 
                                default: latest

    --v|--vv|--vvv              Verbosidad

    -d, --dryrun                Muestra informacion, pero no aplica cambios
    

    """)
    return

def main(argv):

    tag = 'latest'
    cluster = ''
    service = ''
    container = ''
    dry = False
    log_level = logging.ERROR

    try:
        opts, args = getopt.getopt(argv,"dhn:c:s:t:",["v","vv","vvv","dryrun","help","container=","cluster=","service=","tag="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h","--help"):
            print_help()
            sys.exit()
        if opt in ("-d","--dryrun"):
            dry = True
        elif opt in ("-t", "--tag"):
            tag = arg
        elif opt in ("-c", "--cluster"):
            cluster = arg
        elif opt in ("-s", "--service"):
            service = arg
        elif opt in ("-n", "--container"):
            container = arg
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

    if container == '': 
        print ('\nWARN: No se especifico nombre del container, default a %s (service)\n' % service)
        container = service

    if tag == 'latest':
        print ('\nWARN: Deployando version "latest"!\n')

    ecsSupport = EcsSupport(log_level)
    
    try:
        (task_family,task_revision) = ecsSupport.get_task_info(cluster,service)
        print 'Actualmente el servicio %s utiliza la task definition: %s:%s' % (service, task_family, task_revision)
        (image_name,image_tag) = ecsSupport.get_container_info(task_family,task_revision,container)
        if not image_name or not image_tag:
            print ('\nERROR: No se puede obtener la imagen utilizada actualmente para el container %s!' % container)
            sys.exit(2)

        print 'Actualmente el container %s utiliza la imagen: %s:%s' % (container, image_name, image_tag)
        
        if dry :
            print('\nWARN: Dry run, no se ejecutaran cambios! El deploy reemplazaria la imagen %s:%s por la %s:%s para el container %s en la task definition %s en el servicio %s del cluster %s\n' % (image_name,image_tag,image_name,tag,container,task_family,service,cluster))
            sys.exit(0)

        

    except ValueError as (msg):
        print "ERROR: %s" % msg
    except Exception as (msg):
        print "ERROR: {0}".format(msg)

if __name__ == "__main__":
   main(sys.argv[1:])
