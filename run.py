#import os
import sys 
import json
#import argparse 
#import azureml.core
#from azureml.core import Workspace
#from pathlib import Path
from scripts.azure_utils import get_auth, setContext, getWorkspace, getExperiment, registerModel, createImage, createComputeCluster, attachExistingCluster, createWebservice
from scripts.general_utils import loadArguments

from azureml.core.image import ContainerImage


class Context:
    '''
        Model/image information
    '''
    model_file = "model.pkl"
    model_name = 'dummy'
    image_name = "simplemodel"
    scoring_script = "scoring.py"
    '''
        Cluster information
    '''
    aks_name = "dummyaks"
    aks_service_name = "dummycluster"
    aks_vm_size = "Standard_D4_v2"
    aks_node_count = 4
    aks_num_replicas = 2
    aks_cpu_cores = 1

    '''
        Contains the context needed to perform the tasks. 
    '''
    def __init__(self, programArgs, userAuthorization):
        self.programArguments = programArgs
        self.authentication = userAuthorization
        self.workspace = None
        self.experiment = None
        self.model = None
        self.containerImage = None
        self.computeTarget = None
        self.webservice = None
        self.webserviceapi = {}
        

        if not self.authentication:
            raise Exception("Authentication object missing")

        '''
            Change the context to the provided subscription id
            This expects that an az login has already occured with a user
            that has the correct credentials.
        '''
        setContext(self.programArguments.subid)

    def generateWorkspace(self):
        '''
            Gets an existing workspace (by name) or creates a new one
        '''
        
        self.workspace = getWorkspace(
            self.authentication, 
            self.programArguments.subid, 
            self.programArguments.resourceGroup,
            self.programArguments.workspace,
            self.programArguments.region
            )

        if not self.workspace:
            raise Exception("Workspace Creation Failed")

    def generateExperiment(self):
        '''
            Get an existing experiment by name, or create new
        '''
        self.experiment = getExperiment(self.workspace, self.programArguments.experiment)

        if not self.experiment:
            raise Exception("Experiment Creation Failed")

    def generateModel(self):
        '''
            Get an existing model by name or create new
        '''
        self.model = registerModel(
            self.workspace,
            self.experiment,
            Context.model_name,
            Context.model_file
            )

        if not self.model:
            raise Exception("Model Creation Failed")

    def generateImage(self):
        '''
            Generates an image, get name and version using:
            print(image.name, image.version)
            Logs here:
            image.image_build_log_uri
        '''
        self.containerImage = createImage(
            self.workspace,
            Context.scoring_script,
            self.model,
            Context.image_name)

        if not self.containerImage:
            raise Exception("Container Image Creation Failed")

        print("Container Creation Log: ", self.containerImage.image_build_log_uri)

    def loadImage(self):
        '''
            In testing, I did NOT want to keep generating a model and generating an image, 
            if it loads then we've already done that step.
        '''
        if not self.containerImage:
            containers = ContainerImage.list(workspace=program_context.workspace, image_name=Context.image_name)
            if len(containers) > 0:
                print("Found existing image, loading...")
                self.containerImage = containers[-1]

        return self.containerImage != None

    def testImage(self):
        '''
            Test the image locally
        '''   
        if not self.containerImage:
            containers = ContainerImage.list(workspace=program_context.workspace, image_name=Context.image_name)
            if len(containers) > 0:
                self.containerImage = containers[-1]
        
        if self.containerImage:
            result = self.containerImage.run(json.dumps({"name": "Dave"}))
            print("RESULT: ", result)
        else:
            print("No container image found")

    def generateComputeTarget(self, cluster_name = None, resource_group = None):
        '''
            Caller has to figure out if they are going to attach an existing cluster
            or create a new one. Decided based on parameters
        '''

        if self.computeTarget:
            return self.computeTarget

        if cluster_name is None and resource_group is None:
            self.computeTarget = createComputeCluster(
                self.workspace, 
                self.programArguments.region, 
                Context.aks_name, 
                Context.aks_vm_size, 
                Context.aks_node_count
                )
        else:
            self.computeTarget = attachExistingCluster(
                self.workspace, 
                cluster_name, 
                resource_group, 
                Context.aks_name
                )

        if not self.computeTarget:
            raise Exception("Cannot create compute target.")

    def generateWebService(self):
        '''
            Generate the web service
        '''
        if not self.webservice:
            self.webservice = createWebservice(
                self.workspace, 
                self.containerImage,
                Context.aks_service_name, 
                Context.aks_num_replicas, 
                Context.aks_cpu_cores, 
                self.computeTarget
                )

        if not self.webservice:
            raise Exception("Could not create the web service.")

        self.webserviceapi["url"] = self.webservice.scoring_uri
        self.webserviceapi["key"] = self.webservice.get_keys()[0]

    def testWebService(self):
        if self.webservice:
            prediction = self.webservice.run(json.dumps({"name": "Dave"}))
            print(prediction)
'''
    Get the program arguments and user authentication into the context
'''
programargs = loadArguments(sys.argv[1:]) 
userAuth = get_auth()
program_context = Context(programargs, userAuth)


'''
    Get a workspace
'''
program_context.generateWorkspace()

'''
    Get or create an experiment
'''
program_context.generateExperiment()

'''
    Get existing or create and register model
'''
program_context.generateModel()

'''
    Create or update the container image
'''
if program_context.loadImage() == False:
    program_context.generateImage()
    # Does not work on windows
    #program_context.testImage()

'''
    Create/attach existing compute target

    To attach, you have to provide the cluster name and resource group name
    Create service
'''
program_context.generateComputeTarget()

'''
    Create service
'''
program_context.generateWebService()
print(program_context.webserviceapi)
program_context.testWebService()