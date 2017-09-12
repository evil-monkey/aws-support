'''
Created on 09/12/2017

@author:evilmonkey

'''

import json
import exceptions
import subprocess
import os.path
import logging

class EcsSupport():

    def __init__(self, log_level):

        if not log_level:
            log_level = logging.ERROR
        
        logging.basicConfig(level=log_level, format="%(created)-15s %(msecs)d %(levelname)8s %(thread)d %(name)s %(message)s")

        self.log = logging.getLogger(__name__)
        
        whoami,error = self.run_cmd('whoami')
        # looking for aws command on home 
        aws_bin = '/home/%s/.local/bin/aws' % whoami.strip()
        
        if not os.path.isfile(aws_bin) and not os.path.islink(aws_bin):
            raise ValueError('No se encuentra el ejecutable de awscli: %s' % aws_bin)
        
        self.aws_bin = aws_bin

    
    def run_cmd(self,cmd):

        try:
    	      process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    	      output, error = process.communicate()
    	      self.log.debug('\nRunning command: %s\noutput: %s\nerror: %s\n' % (cmd,output,error)) 
    	      return output, error
        except exceptions.OSError as (errno, strerror):
            print "OSError({0}): {1}".format(errno, strerror)
        except:
            print "ERROR:", sys.exc_info()   
            raise

    
    def version(self):

        version_command = '%s --version' % self.aws_bin
        
        output, error = self.run_cmd(version_command)

        if not error:
            raise Exception("ERROR: error al intentar comprobar la version del cliente de AWS")

        return error

    
    def deploy(self,cluster,service,tag):

        self.log.info(self.version())
        print('\nDesplegando:\n\tcluster=%s,\n\tservice=%s,\n\ttag=%s\n' % (cluster,service,tag)) 

        service_describe_command = '%s ecs describe-services --services %s --cluster %s' % (self.aws_bin,service,cluster) 
        print service_describe_command
        output, error = self.run_cmd(service_describe_command)
        if not error:
	          service_description = json.loads(output)
	          task_definition = service_description['services'][0]['taskDefinition']
	          task_family, task_revision = task_definition.split(':')[-2:]
	          task_family = task_family.split('/')[-1:][0]
	          print 'Actualmente el servicio %s utiliza la task definition: %s:%s' % (service, task_family, task_revision)
        else:
            print "ERROR: error al intentar comprobar la version del cliente de AWS: %s".format(error)
            raise Exception(error)


