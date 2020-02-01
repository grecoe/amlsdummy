#import os
import sys 
import json
#import argparse 
#import azureml.core
#from azureml.core import Workspace
#from pathlib import Path
from scripts.azure_utils import get_auth, setContext, getWorkspace, getExperiment, registerModel, createImage
from scripts.general_utils import loadArguments

from azureml.core.image import ContainerImage


class Context:
    model_file = "model.pkl"
    model_name = 'dummy'
    image_name = "simplemodel"
    scoring_script = "scoring.py"

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

    def testImage(self):
        '''
            Test the image locally
        '''   
        image_to_test = self.containerImage
        if not image_to_test:
            containers = ContainerImage.list(workspace=program_context.workspace, image_name=Context.image_name)
            if len(containers) == 1:
                image_to_test = containers[0]
        
        if image_to_test:
            result = image_to_test.run(json.dumps({"name": "Dave"}))
            print("RESULT: ", result)
        else:
            print("No container image found")
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
program_context.generateImage()
program_context.testImage()

# Now you can access your arguments as attributes.  
'''
print(program_context.programArguments.subid) 
print(program_context.programArguments.resourceGroup) 
print(program_context.programArguments.region) 
print(program_context.programArguments.workspace) 
print(program_context.programArguments.useExistingWorkspace) 
print(program_context.authentication)
'''

 
