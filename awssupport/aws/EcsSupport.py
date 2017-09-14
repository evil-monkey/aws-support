'''
Created on 09/12/2017

@author:evilmonkey

'''

import os
import uuid
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
        self.log.info(self.version())

    
    def run_cmd(self,cmd):

        try:
    	      process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    	      output, error = process.communicate()
    	      self.log.debug('\nRunning command: %s\noutput: %s\nerror: %s\n' % (cmd,output,error)) 
    	      return output, error
        except exceptions.OSError as (errno, strerror):
            self.log.error("OSError({0}): {1}".format(errno, strerror))
            raise
        except:
            self.log.error("ERROR:", sys.exc_info())   
            raise

    
    def version(self):

        version_command = '%s --version' % self.aws_bin
        
        output, error = self.run_cmd(version_command)

        if not error:
            raise Exception("ERROR: error al intentar comprobar la version del cliente de AWS")

        return error

    
    def get_task_info(self,cluster,service):

        service_describe_command = '%s ecs describe-services --services %s --cluster %s' % (self.aws_bin,service,cluster) 
        self.log.info(service_describe_command)
        output, error = self.run_cmd(service_describe_command)
        if not error:
	          service_description = json.loads(output)
	          task_definition = service_description['services'][0]['taskDefinition']
	          task_family, task_revision = task_definition.split(':')[-2:]
	          task_family = task_family.split('/')[-1:][0]
	          return (task_family,task_revision)
        else:
            self.log.error("ERROR: error al intentar obtener la descripcion del servicio: %s" % error)
            raise Exception(error)
    
    
    def get_container_info(self,task_family,task_revision,container):

        task_describe_command = '%s ecs describe-task-definition --task-definition %s:%s' % (self.aws_bin,task_family,task_revision) 
        self.log.info(task_describe_command)
        output, error = self.run_cmd(task_describe_command)
        if not error:
	          (image_name,image_tag) = (None,None)
	          task_description = json.loads(output)
	          containers = task_description['taskDefinition']['containerDefinitions']
	          containerDefinition = None
	          index = len(containers) - 1
	          
	          while( not containerDefinition and  index > -1):
	              if containers[index]['name'] == container:
	                  containerDefinition = containers[index]
	              index-=1
	          
	          if containerDefinition:
	              (image_name,image_tag) = containerDefinition['image'].split(':')

	          return (image_name,image_tag,containers)
        else:
            self.log.error("ERROR: error al intentar obtener la task definition: %s" % error)
            raise Exception(error)
   

    def create_task_revision(self,from_family, containers, containers_map):

        for container in containers:
            self.log.debug('Actualizando container %s...' % container['name'])
            if container['name'] in containers_map:
                image_parts = container['image'].split(':')
                image_parts[-1] = containers_map[container['name']]
                container['image'] = ":".join(image_parts)
                self.log.debug('... nueva imagen para %s: %s' % (container['name'],container['image']))

        #print containers
        tempfile = '/tmp/%s.json' % str(uuid.uuid4())
        container_definitions = { "containerDefinitions": containers }
        self.log.debug("Nueva definicion de containers: %s" % json.dumps(container_definitions))

        with open(tempfile, 'w') as outfile:
            json.dump(container_definitions, outfile)

        self.log.debug('New container definitions for task %s: %s' % (from_family,container_definitions))

        register_task_command = "%s ecs register-task-definition --family %s --cli-input-json file://%s" % (self.aws_bin,from_family,tempfile) 
        
        self.log.info(register_task_command)
        output, error = self.run_cmd(register_task_command)
        os.remove(tempfile)

        if not error:
	          result = json.loads(output)
	          task_definition_arn = result['taskDefinition']['taskDefinitionArn']
	          task_revision = task_definition_arn.split(':')[-1]
	          return str(task_revision)
        else:
            self.log.error("ERROR: error al intentar comprobar la version del cliente de AWS: %s" % error)
            raise Exception(error)
    

    def update_service(self,cluster,service,task_family,task_revision):

        service_update_command = '%s ecs update-service --cluster %s --service %s --task-definition %s:%s' % (self.aws_bin,cluster,service,task_family,task_revision) 
        self.log.info(service_update_command)
        output, error = self.run_cmd(service_update_command)
        if not error:
	          service_description = json.loads(output)
	          task_definition = service_description['service']['taskDefinition']
	          service_name = service_description['service']['serviceName']

	          return (service_name, task_definition)
        else:
            self.log.error("ERROR: error al intentar obtener la task definition: %s" % error)
            raise Exception(error)
