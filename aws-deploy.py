#!/usr/bin/python

import sys, getopt, subprocess, exceptions, json

def print_help():
    print( """usage: aws-deploy.py [--help]
        [-c=cluster] [-s=service] [-t=tag]

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
    
    """)
    return

def main(argv):

    tag = 'latest'
    cluster = ''
    service = ''

    try:
        opts, args = getopt.getopt(argv,"hc:s:t:",["help","cluster=","service=","tag="])
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

    if cluster == '' or service == '':
        print ('\nERROR: cluster y service deben ser especificados.\n')
	print_help()
	sys.exit(2)

    if tag == 'latest':
        print ('\nWARN: Deployando version "latest"!\n')
	
    try_deploy(cluster,service,tag)

def try_deploy(cluster,service,tag):

    print('\nDesplegando:\n\tcluster=%s,\n\tservice=%s,\n\ttag=%s\n' % (cluster,service,tag)) 
    aws_bin = '/home/gitlab-runner/.local/bin/aws'
    version_command = '%s --version' % aws_bin
    
    output, error = run_cmd(version_command)

    if not error:
	print output
    else:
        print "ERROR: error al intentar comprobar la version del cliente de AWS: %s".format(error)
	sys.exit(2)

    service_describe_command = '%s ecs describe-services --services %s --cluster %s' % (aws_bin,service,cluster) 
    print service_describe_command
    output, error = run_cmd(service_describe_command)
    if not error:
	service_description = json.loads(output)
        task_definition = service_description['services'][0]['taskDefinition']
	task_family, task_revision = task_definition.split(':')[-2:]
	task_family = task_family.split('/')[-1:][0]
	print 'Actualmente el servicio %s utiliza la task definition: %s:%s' % (service, task_family, task_revision)
    else:
        print "ERROR: error al intentar comprobar la version del cliente de AWS: %s".format(error)
	sys.exit(2)
    

def run_cmd(cmd):

    try:
    	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    	output, error = process.communicate()
        return output, error
    except exceptions.OSError as (errno, strerror):
        print "OSError({0}): {1}".format(errno, strerror)
        sys.exit(2)
    except:
	print "ERROR:", sys.exc_info()     
        sys.exit(2)

if __name__ == "__main__":
   main(sys.argv[1:])
