import requests
import json
import os

from azureml.core import Workspace
from azureml.core import Experiment
from azureml.core import Model
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.authentication import AzureCliAuthentication
from azureml.core.authentication import InteractiveLoginAuthentication
from azureml.core.authentication import AuthenticationException
from azureml.core.compute import AksCompute, AmlCompute, ComputeTarget
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.datastore import Datastore
from azureml.core.image import ContainerImage
from azureml.core.webservice import Webservice, AksWebservice
from azureml.data.data_reference import DataReference
from azureml.pipeline.core import Pipeline, PipelineData, PublishedPipeline
from azureml.pipeline.core.schedule import ScheduleRecurrence, Schedule

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient
from scripts.general_utils import createPickle


def get_auth():
    '''
        Retreive the user authentication. If they aren't logged in this will
        prompt the standard interactive login method. 

        PARAMS: None

        RETURNS: Authentication object
    '''
    auth = None
    
    print("Get auth...")
    try:
        auth = AzureCliAuthentication()
        auth.get_authentication_header()
    except AuthenticationException:
        auth = InteractiveLoginAuthentication()

    return auth

def setContext(subscription_id):
    '''
        Using the 'az account set' api, change the current subscription
        context to the requested subscription so that future calls happen
        in the requested subscription. 

        PARAMS: 
            subscription_id : String : Azure Subscription ID

        RETURNS: NONE

        THROWS:
            Exception if output is not empty. As of the writing of this 
            a succesful call has no output. 
    '''
    print("Setting context....")

    set_command = "az account set --subscription " + subscription_id
    stream = os.popen(set_command)
    output = stream.read()

    if len(output) != 0:
        raise Exception("Context Exception : " + output)

def getWorkspace(authentication, subscription_id, resource_group, workspace_name,  workspace_region):
    '''
        Obtains an existing workspace, or creates a new one. If a workspace exists in the subscription
        in the same resource group, with the same name it is returned, otherwise, a new one is created.

        PARAMS: 
            authentication   : azureml.core.authentication   : User Authentication with rights to sub 
            subscription_id  : String                        : Azure Subscription ID
            resource_group   : String                        : Azure Resource Group Name
            workspace_name   : String                        : AMLS workspace name
            workspace_region : String                        : Azure Region


        RETURNS: 
            azureml.core.Workspace
    '''
    return_workspace = None
    useExistingWorkspace = False
    workspaces = None
    
    '''
        If resource group doesn't exist, this will throw a ProjectSystemException  
    '''
    try:
        workspaces = Workspace.list(subscription_id, authentication, resource_group )
    except Exception as ex:
        workspaces = None

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
        print("Loading existing workspace ....", workspace_name)
        return_workspace = Workspace.get(
            name = workspace_name,
            subscription_id = subscription_id,
            resource_group = resource_group
            )
    else:
        # Create one
        print("Creating new workspace ....", workspace_name)
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
        Gets an AMLS experiment. Searches through the provided workspace experiments first
        to see if it already exists. If not, create a new one, otherwise return the existing one. 

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            experiment_name  : String                   : Name of experiment to retrieve/create

        RETURNS: 
            azureml.core.Experiment
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
    '''
        Search an existing AMLS workspace for models. If one is found, return it, 
        otherwise create a new model. 

        If the parameter model_file points to a file on disk (check existence), then that
        is used to register a new model. If not, a new dummy pkl file will be generated. 

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            experiment_name  : azureml.core.Experiment  : Existing AMLS Experiment
            model_name       : String                   : The name of the model to register
            model_file       : String                   : This is one of two values
                                                            1. Name of a pkl file to create (dummy for RTS)
                                                            2. Full path to pkl model file that is in the same 
                                                               directory as the running script. 


        RETURNS: 
            azureml.core.Model
    '''

    return_model = None

    '''
        If model already exists then just return it. 
    '''
    models = Model.list(workspace)
    if models:
        for model in models:
            if model.name == model_name:
                print("Returning existing model....", model_name)
                return_model = model
                break

    if not return_model:
        '''
            Create it. 
        '''
        print("Creating new  model....")
        run = experiment.start_logging()
        run.log("Just simply dumping somethign in", True)

        # If the file does not exist, create a dummy model file. 
        if os.path.exists(model_file) == False:
            createPickle(model_file)

        run.upload_file(name = 'outputs/' + model_file, path_or_stream = './'+ model_file)

        # Complete tracking and get link to details
        details = run.complete()

        return_model = run.register_model(model_name = model_name, model_path = "outputs/" + model_file)

    return return_model

def createImage(workspace, scoring_file, model, image_name ):
    '''
        TODO: We should probably allow the conda_pack/requirements to be identified so we can switch
              between CPU/GPU

        NOTE: This function doesn't check for the existence of an image because new builds 
              will just create a new version on a container. If the caller doesn't want duplicates, 
              they need to ensure that one does not exist already.


        Creates a new Docker Container image and uploads it to the associated ACR 
        with the workspace. 

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            scoring_file     : String                   : Name/path of local .py file that has an init() and run() function defined.
            model            : azureml.core.Model       : Registered AMLS model
            image_name       : String                   : Name of the container to be created.


        RETURNS: 
            azureml.core.image.ContainerImage
    '''
    
    conda_pack = []
    requirements = ["azureml-defaults==1.0.57", "azureml-contrib-services"]

    print("Creating image...")

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
    print("Image created IMAGE/VERSION: " , image.name, '/',  image.version)
    
    return image

def _getExistingCompute(workspace, compute_name):
    '''
        Tries to load an existing AMLS compute target by name searching
        a specified AMLS workspace

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            compute_name     : String                   : Name of the AMLS compute to locate.


        RETURNS: 
            azureml.core.compute.ComputeTarget or None if not found
    '''
    existing_compute = None

    targets = ComputeTarget.list(workspace)
    if len(targets) > 0:
        for target in targets:
            if target.name == compute_name:
                print("Found existing compute with name ", compute_name)
                existing_compute = target
                break

    return existing_compute

def _getClusterPurpose(dev_test):
    '''
        For an explaination on this field, see:

        https://docs.microsoft.com/en-us/python/api/azureml-core/azureml.core.compute.aks.akscompute.clusterpurpose?view=azure-ml-py

        PARAMS: 
            dev_test        : bool   : Flag indicating if this is a development cluster.


        RETURNS: 
            String AksCompute.ClusterPurpose depending on purpose. 
    '''
    purpose = AksCompute.ClusterPurpose.FAST_PROD
    if dev_test:
        purpose = AksCompute.ClusterPurpose.DEV_TEST
    return purpose

def createBatchComputeCluster(workspace, compute_name, compute_sku, max_node_count, min_node_count):
    '''
        Create new AKS cluster, unless there is an existing AMLS compute with the same 
        name already attached to the AMLS workspace. 

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            compute_name     : String                   : Name of the AMLS compute to create/locate.
            compute_sku      : String                   : Azure ML VM Sku
            max_node_count   : int                      : Max number of VM's to add to the cluster
            min_node_count   : int                      : Min number of VM's to add to the cluster

        RETURNS: 
            azureml.core.compute.ComputeTarget

    '''
    batch_target = _getExistingCompute(workspace, compute_name)
    
    if batch_target == None:
        print("Creating new Batch compute.....")
        prov_config = AmlCompute.provisioning_configuration(
            vm_size = compute_sku, 
            min_nodes = min_node_count,
            max_nodes = max_node_count
            )
 
        batch_target = ComputeTarget.create(
            workspace = workspace, 
            name = compute_name, 
            provisioning_configuration = prov_config
        )

        batch_target.wait_for_completion(show_output = True)

        batch_status = batch_target.get_status()
        print("Batch Compute Status : ", batch_status)

    return batch_target

def createComputeCluster(workspace, region, compute_name, compute_sku, node_count, dev_cluster):
    '''
        Create new AKS cluster, unless there is an existing AMLS compute with the same 
        name already attached to the AMLS workspace. 

        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            region           : String                   : Azure region
            compute_name     : String                   : Name of the AMLS compute to create/locate.
            compute_sku      : String                   : Azure ML VM Sku
            node_count       : int                      : Number of VM's to add to the cluster
            dev_cluster      : bool                     : Flag indicating if this is a development cluster. A development
                                                          cluster generally has fewwer vCPU's based on node count than allowed
                                                          for a production deployment. 

        RETURNS: 
            azureml.core.compute.AksCompute

    '''
    purpose = _getClusterPurpose(dev_cluster)
    aks_target = _getExistingCompute(workspace, compute_name)
    
    if aks_target == None:
        print("Creating new AKS compute.....")
        prov_config = AksCompute.provisioning_configuration(
            agent_count = node_count, 
            vm_size = compute_sku, 
            location = region,
            cluster_purpose = purpose
            )
 
        aks_target = ComputeTarget.create(
            workspace = workspace, 
            name = compute_name, 
            provisioning_configuration = prov_config
        )

        aks_target.wait_for_completion(show_output = True)

        aks_status = aks_target.get_status()
        assert aks_status == 'Succeeded'

    return aks_target

def attachExistingCluster(workspace, cluster_name, resource_group, compute_name, dev_cluster):
    '''
        Attach an existing AKS cluster, unless there is an existing AMLS compute with the same 
        name already attached to the AMLS workspace. 


        PARAMS: 
            workspace        : azureml.core.Workspace   : Existing AMLS Workspace
            cluster_name     : String                   : Name of an existing AKS cluster 
            resource_group   : String                   : Name of the Azure Resource group existing cluster is in
            compute_name     : String                   : Name of the AMLS compute to create/locate.
            dev_cluster      : bool                     : Flag indicating if this is a development cluster. A development
                                                          cluster generally has fewwer vCPU's based on node count than allowed
                                                          for a production deployment. 

        RETURNS: 
            azureml.core.compute.AksCompute

    '''
    print("Attaching existing AKS compute.....")

    purpose = _getClusterPurpose(dev_cluster)
    aks_target = _getExistingCompute(workspace, compute_name)

    if aks_target == None:
        attach_config = AksCompute.attach_configuration(
            resource_group = resource_group,
            cluster_name = cluster_name,
            cluster_purpose = purpose
            )
    
        if attach_config:
            aks_target = ComputeTarget.attach(workspace, compute_name, attach_config)

    return aks_target

def createWebservice(workspace, container_image, service_name, replica_count, cores_count, compute_target):
    '''
        TODO: Should allow for the overwrite flag. 

        Attach a azureml.core.webservice.Webservice for a given container on an AKS cluster. 

        If a WebService already exists (by name) on the given workspace, return it instead. 


        PARAMS: 
            workspace        : azureml.core.Workspace               : Existing AMLS Workspace
            container_image  : azureml.core.image.ContainerImage    : Name of an existing AKS cluster 
            service_name     : String                               : Name of the webservice (deployment) in the AMLS workpsace.
            replica_count    : int                                  : Number of requested instances of container on cluster.
            cores_count      : int                                  : Number of cores to allocate to each container
            compute_target   : azureml.core.compute.AksCompute      : AKS cluster to create the service on

        RETURNS: 
            azureml.core.webservice.Webservice

    '''
    web_service = None

    services = Webservice.list(workspace = workspace, image_name = container_image.name)
    if len(services) > 0:
        for svc in services:
            if svc.name == service_name:
                print("Returning existing deployed web service ....", service_name)
                web_service = svc
                break

    if web_service == None:
        print("Creating new web service.....", service_name)
        aks_config = AksWebservice.deploy_configuration(num_replicas=replica_count, cpu_cores=cores_count)

        web_service = Webservice.deploy_from_image(
            workspace = workspace,
            name = service_name,
            image = container_image,
            deployment_config = aks_config,
            deployment_target = compute_target,
            )
    
        web_service.wait_for_deployment(show_output=True)

    return web_service

# Batch Specific calls
def createStorageContainer(storage_name, storage_key, container_names):
    '''
        Create storage containers in the provided storage account. If the containers 
        exist, they will not be altered.

        PARAMS: 
            storage_name     : string       : Name of the Azure Storage Account
            storage_key      : string       : Access Key to the Azure Storage Account
            container_names  : list[string] : List of container names to create.

        RETURNS: 
            Nothing

    '''
    
    blob_service = BlobServiceClient(account_url="https://"+storage_name+".blob.core.windows.net/", credential=storage_key)

    for container in container_names:
        try:
            blob_service.create_container(container)
            print("Storage container created - ", storage_name, " : ", container)
        except ResourceExistsError: 
            print("Storage container already exists - ", storage_name, " : ", container)

def uploadStorageBlobs(storage_name, storage_key, container_name, local_folder, file_list):
    '''
        Upload files to an azure blob container.

        PARAMS: 
            storage_name     : string       : Name of the Azure Storage Account
            storage_key      : string       : Access Key to the Azure Storage Account
            container_name   : string       : Container name to recieve blobs. Must exist
            local_folder     : string       : Local folder containing files to upload.
            file_list  : list[string] : List of files from local folder to upload

        RETURNS: 
            Nothing

    '''
    
    blob_service = BlobServiceClient(account_url="https://"+storage_name+".blob.core.windows.net/", credential=storage_key)
    blob_container = blob_service.get_container_client(container_name)
    for local_file in file_list:
        path = os.path.join(local_folder, local_file)
        with open(path, "rb") as data:    
            try:
                blob_container.upload_blob(local_file, data)
                print("File Uploaded : ", container_name,'-',local_file)
            except ResourceExistsError: 
                print("File Exists : ", container_name,'-',local_file)

def createDataReference(workspace, storage_name, storage_key, storage_container_name, data_store_name, data_reference_name):
    '''
        If no present, registers a new azureml.core.datastore.Datastore
        Once the data store is in hand it creates an instance of azureml.data.data_reference.DataReference that 
        can be used in an Azure ML pipeline step. 

        PARAMS: 
            workspace               : azureml.core.Workspace    : Existing AMLS Workspace
            storage_name            : string                    : Name of the Azure Storage Account
            storage_key             : string                    : Access Key to the Azure Storage Account
            storage_container_name  : string                    : Container name to recieve blobs. Must exist
            data_store_name         : string                    : Name of the registere data store.
            data_reference_name     : string                    : Name of the data reference

        RETURNS: 
            tuple(azureml.core.datastore.Datastore, azureml.data.data_reference.DataReference)

    '''
    data_store = None

    try:
        data_store = Datastore.get(workspace, data_store_name)
        print("Found existing data store - ", data_store_name)
    except Exception as ex:
        print("Creating data store - ", data_store_name)
        
        data_store = Datastore.register_azure_blob_container(
                    workspace,
                    datastore_name=data_store_name,
                    container_name=storage_container_name,
                    account_name=storage_name,
                    account_key=storage_key,
                )

    if data_store == None:
        raise Exception("Could not create/find data store.")

    return  data_store, DataReference(datastore = data_store, data_reference_name = data_reference_name)

def getExistingPipeline(workspace, pipeline_name):
    '''
        Look for an return an exising azureml.pipeline.core.PublishedPipeline instance based on name 

        PARAMS: 
            workspace               : azureml.core.Workspace    : Existing AMLS Workspace
            pipeline_name           : string                    : Name of the published pipeline to find.

        RETURNS: 
            azureml.pipeline.core.PublishedPipeline if found, None otherwise

    '''
    return_pipeline = None

    pipelines = PublishedPipeline.list(workspace)
    if len(pipelines) > 0:
        for pipe in pipelines:
            if pipe.name == pipeline_name:
                return_pipeline = pipe 
                break

    return return_pipeline