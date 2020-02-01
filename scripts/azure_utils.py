import re
import math
import gzip
import requests
import json
import os
from azureml.core import Workspace
from azureml.core import Experiment
from azureml.core import Model
from azureml.core.image import ContainerImage

from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.authentication import AzureCliAuthentication
from azureml.core.authentication import InteractiveLoginAuthentication
from azureml.core.authentication import AuthenticationException

from azureml.core.conda_dependencies import CondaDependencies

from scripts.general_utils import createPickle

'''
def text_to_json(text):
    return json.dumps({'input': '{0}'.format(text)})


def write_json_to_file(json_dict, filename, mode='w'):
    with open(filename, mode) as outfile:
        json.dump(json_dict, outfile, indent=4, sort_keys=True)
        outfile.write('\n\n')
'''

def get_auth():
    auth = None
    
    print("Get auth...")
    try:
        auth = AzureCliAuthentication()
        auth.get_authentication_header()
    except AuthenticationException:
        auth = InteractiveLoginAuthentication()

    return auth

def setContext(subscription_id):
    set_command = "az account set --subscription " + subscription_id
    print("Setting context....")
    stream = os.popen(set_command)
    output = stream.read()
    assert(len(output) == 0)

def getWorkspace(authentication, subscription_id, resource_group, workspace_name,  workspace_region):
    '''
        Obtains an existing workspace, or creates a new one. If a workspace exists with the same
        name it is returned, otherwise, a new one is created.

        Could also persist workspace:
        ws.write_config(path="./file-path", file_name="ws_config.json")

        Load saved one:
        ws = Workspace.from_config()

        Get Details:
        ws.get_details()
    '''
    return_workspace = None
    useExistingWorkspace = False
    workspaces = Workspace.list(subscription_id, authentication, resource_group )

    '''
        See if it already exists
    '''
    if workspaces:
        for ws in workspaces.keys():
            if ws == workspace_name:
                useExistingWorkspace = True

    '''
        Return existing or create new
    '''
    if useExistingWorkspace:
        print("Loading existing workspace ....")
        return_workspace = Workspace.get(
            name = workspace_name,
            subscription_id = subscription_id,
            resource_group = resource_group
            )
    else:
        # Create one
        print("Creating new workspace ....")
        return_workspace = Workspace.create(
            name = workspace_name,
            subscription_id = subscription_id,
            resource_group = resource_group,
            create_resource_group = True,
            location = workspace_region
            )

    return return_workspace #  program_context.workspace.get_details() 

def getExperiment(workspace, experiment_name):
    '''
        Gets an AMLS experiment. Searches through existing experiments first
        to see if it already exists. If not, create a new one, otherwise
        return the existing one. 
    '''
    found = False
    return_experiment = None
    for experiment in Experiment.list(workspace):
        if experiment.name == experiment_name:
            print("Returning existing experiment", experiment_name)
            found = True
            return_experiment = experiment

    if not found:
        print("Creating new experiment", experiment_name)
        return_experiment = Experiment(workspace, experiment_name)

    return return_experiment

def registerModel(workspace, experiment, model_name, model_file):

    return_model = None

    '''
        If model already exists then just return it. 
    '''
    models = Model.list(workspace)
    if models:
        for model in models:
            if model.name == model_name:
                print("Returning existing model....")
                return_model = model
                break

    if not return_model:
        '''
            Create it. 
        '''
        print("Creating new  model....")
        run = experiment.start_logging()
        run.log("Just simply dumping somethign in", True)

        createPickle(model_file)

        run.upload_file(name = 'outputs/' + model_file, path_or_stream = './'+ model_file)

        # Complete tracking and get link to details
        details = run.complete()
        print(details)

        return_model = run.register_model(model_name = model_name, model_path = "outputs/" + model_file)

    return return_model

def createImage(workspace, scoring_file, model, image_name ):
    conda_pack = []
    requirements = ["azureml-defaults==1.0.57", "azureml-contrib-services"]

    simple_environment = CondaDependencies.create(conda_packages=conda_pack, pip_packages=requirements)

    with open("simple.yml", "w") as f:
        f.write(simple_environment.serialize_to_string())

    image_config = ContainerImage.image_configuration(
        execution_script = scoring_file,
        runtime = "python",
        conda_file = "simple.yml",
        description = "Image with dummy (unused) model",
        tags={"type": "noop"},
        dependencies=[]
    )

    image = ContainerImage.create(
        name = image_name,
        models = [model],
        image_config = image_config,
        workspace = workspace,
    )

    image.wait_for_creation(show_output = True)
    print("IMAGE/VERSION: " , image.name, image.version)
    
    return image