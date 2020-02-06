'''
    Program Code: Create Azure Machine Learning Real Time Scoring Service

    Program will use settings from argument.py where user can optionally pass in parameters or 
    use the defaults set up. Those parameters and the user authentication are held in the Context class
    defined above. 

    Since this can be run in steps to slowly build up the service (as I did when creating this), each step
    validates if the object or service needs to be created. If it already exists (generally based on name)
    a new object/service is not created and the existing object/service is preserved in the Context class.

    Also note, each step needs to be performed in order (listed here) so that the appropriate objects/services
    are collected before trying to use them. 
'''
import os
import sys 
import json
from scripts.azure_utils import get_auth
from contexts.rtscontext import RealTimeScoringContext
from scripts.argument_utils import ExperimentType, loadConfiguration

'''
    Get the program arguments and user authentication into the context
'''
programargs = loadConfiguration(ExperimentType.real_time_scoring,sys.argv[1:])
userAuth = get_auth()
program_context = RealTimeScoringContext(programargs, userAuth)


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
    program_context.testImage()

'''
    Create/attach existing compute target

    To attach, you have to provide the cluster name and resource group name
    in the program arguments. By default they are set to None so that a new cluster
    is generated.
'''
program_context.generateComputeTarget(
     cluster_name = program_context.programArguments.aks_existing_cluster,
     resource_group = program_context.programArguments.aks_existing_rg
     )

'''
    Create service
'''
program_context.generateWebService()
print(program_context.webserviceapi)
program_context.testWebService()

'''
    Clean up temporary files
'''
temp_files = ["simple.yml", "model.pkl"]
for f in temp_files:
    if os.path.exists(f):
        os.remove(f)
