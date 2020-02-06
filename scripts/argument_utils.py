import sys 
import argparse 
import os
import json
from enum import Enum

class ExperimentType(Enum):
    real_time_scoring = 1,
    batch_scoring = 2

def _loadUserConfiguration(configuration_file):
    '''
        If the program is started with two arguments:
            -config [filename]
        
        The settings for the program will strictly be loaded from the provided configuration
        file (JSON), bypassing any other provided arguments AND the default settings in xxLoadArguments()

        When reading in a json null, Python converts it to the string None. Make sure we catch these. 

        PARAMETERS:
            configuration_file  : String    : JSON file containing the configuraiton

        RETURNS:
            List of settings as would be seen on the command line i.e. ['-op', 'value']
    '''
    return_settings = []
    config_json = None
    if configuration_file:
        if os.path.exists(configuration_file) :
            with open(configuration_file,"r") as input_config:
                config_content = input_config.read()
                config_json = json.loads(config_content)

    for key in config_json:
        return_settings.append('-' + key)
        value = config_json[key]
        if value == None or value == 'None':
            return_settings.append(None)
        else:
            return_settings.append(str(value))

    return return_settings


def loadConfiguration(experimentType, system_arguments):

    arguments = system_arguments.copy()

    if '-config' in arguments and len(arguments) == 2:
        print("Load configuration settings file : " , arguments[1])
        arguments = _loadUserConfiguration(arguments[1])

    parsed_arguments = None
    if experimentType == ExperimentType.real_time_scoring:
        parsed_arguments = _loadRtsArguments(arguments)
    elif experimentType == ExperimentType.batch_scoring:
        parsed_arguments = _loadBatchArguments(arguments)
    else:
        raise Exception("Unknown experiment type passed to load configuration")

    return parsed_arguments


def _loadBatchArguments(sys_args):
    '''
        Loads the arguments for the program for the RTS scoring path.. 
        User has the choice to:
        1. Provide no arguments -> Use defaults in this function
        2. -config [filename] as the only 2 arguments -> Load the settings from the configuration file
        3. Multiple arguments -> Use the provided arguments
    '''
    if len(sys_args) == 0:
        print("Using default settings in _loadBatchArguments()")
    else:
        print("User provided settings and or configuration file will be used in _loadBatchArguments().")

    '''
        All of the parameters needed to execute a succesful deployment. These can simply be set here 
        so that you can run run.py without any additional parameters OR you can pass in one or many settings.
    '''
    parser = argparse.ArgumentParser(description='Batch Scoring model deployment.') 

    '''
        Subscription information : Subscription ID, Resource Group, Region
    '''
    parser.add_argument("-subid", required=False, default='0ca618d2-22a8-413a-96d0-0f1b531129c3', type=str, help="Subscription ID") 
    parser.add_argument("-resourceGroup", required=False, default="dangtestbedbatch", type=str, help="Resource Group") 
    parser.add_argument("-region", required=False, default="eastus", type=str, help="Azure Region") 

    '''
        AMLS Workspace infomration: workspace name
    '''
    parser.add_argument("-workspace", required=False, default="dangwsbtch", type=str, help="Workspace name") 
    '''
        AMLS Exeriment informaiton:
            - Experiment name
            - Model name (that will be registered)
    '''
    parser.add_argument("-experiment", required=False, default="simple_experiment", type=str, help="Experiment name") 
    parser.add_argument("-model_name", required=False, default="dummy", type=str, help="Registered model name") 

    '''
        AMLS Compute Information
    '''
    parser.add_argument("-batch_compute_name", required=False, default="dummybatch", type=str, help="AMLS Compute Name") 
    parser.add_argument("-batch_vm_size", required=False, default="Standard_D2", type=str, help="Azure VM SKU") 
    parser.add_argument("-batch_vm_min", required=False, default=2, type=int, help="Min Azure VM count") 
    parser.add_argument("-batch_vm_max", required=False, default=2, type=int, help="Max Azure VM count") 


    parser.add_argument("-source_blob_account", required=False, default="FINDREAL", type=str, help="AMLS Compute Name") 
    parser.add_argument("-source_blob_key", required=False, default="FINDREAL", type=str, help="AMLS Compute Name") 


    parsed_arguments = parser.parse_args(sys_args)
    '''
        For some reason, when loading from JSON and leaving None in the 
        input array for parser.parse_args, those values are getting turned 
        into the String None, correct that here.
    '''
    for attr, value in parsed_arguments.__dict__.items():
        if value == 'None':
            setattr(parsed_arguments, attr, None)


    return parsed_arguments    


def _loadRtsArguments(sys_args):
    '''
        Loads the arguments for the program for the RTS scoring path.. 
        User has the choice to:
        1. Provide no arguments -> Use defaults in this function
        2. -config [filename] as the only 2 arguments -> Load the settings from the configuration file
        3. Multiple arguments -> Use the provided arguments
    '''
    if len(sys_args) == 0:
        print("Using default settings in _loadRtsArguments()")
    else:
        print("User provided settings and or configuration file will be used in _loadRtsArguments().")

    '''
        All of the parameters needed to execute a succesful deployment. These can simply be set here 
        so that you can run run.py without any additional parameters OR you can pass in one or many settings.
    '''
    parser = argparse.ArgumentParser(description='Real Time Scoring model deployment.') 

    '''
        Subscription information : Subscription ID, Resource Group, Region
    '''
    parser.add_argument("-subid", required=False, default='0ca618d2-22a8-413a-96d0-0f1b531129c3', type=str, help="Subscription ID") 
    parser.add_argument("-resourceGroup", required=False, default="dangtestbed", type=str, help="Resource Group") 
    parser.add_argument("-region", required=False, default="eastus", type=str, help="Azure Region") 
    '''
        AMLS Workspace infomration: workspace name
    '''
    parser.add_argument("-workspace", required=False, default="dangws", type=str, help="Workspace name") 
    '''
        AMLS Exeriment informaiton:
            - Experiment name
            - Model name (that will be registered)
            - Docker container image name
    '''
    parser.add_argument("-experiment", required=False, default="simple_experiment", type=str, help="Experiment name") 
    parser.add_argument("-model_name", required=False, default="dummy", type=str, help="Registered model name") 
    parser.add_argument("-image_name", required=False, default="simplemodel", type=str, help="Docker container name")
    '''
        AKS Information

            Information for adding or attaching an AKS cluster as an Inference Compute to 
            the AMLS workpsace. 

            IMPORTANT : If aks_existing_cluster and aks_existing_rg are NOT None, then 
                        the program will try and attach, not create a new cluster. 

            COMMON FIELDS - ADD OR ATTACH
                - aks_compute_name - AKS Compute name in AMLS Workspace
                - aks_service_name - AKS Service name (the name of the generated webservice)
                - aks_non_prod - If this flag is set AND the cluster is to be created or attached
                        then the configuration will include the following flag:
                            cluster_purpose = AksCompute.ClusterPurpose.DEV_TEST
                        Essentially, this means that the cluster you are attaching or requesting 
                        would not be suitable for production. For more information see here:

                        https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-azure-kubernetes-service#create-a-new-aks-cluster

            ATTACH CLUSTER INFORMATION
                - aks_existing_cluster - Name of an existing AKS cluster to attach
                - aks_existing_rg - Resource group in which the existing cluster lives in.

            CREATE CLUSTER INFORMATION
                - aks_vm_size - The type of VM to create the cluster with
                - aks_node_count - The number of VM's to add to the cluster
                - aks_num_replicas - The number of instances of the container running in the cluster.
                - aks_cpu_cores - Number of cores to allocate to each replica
    ''' 
    # Common
    parser.add_argument("-aks_compute_name", required=False, default="dummyaks", type=str, help="AMLS Compute Name") 
    parser.add_argument("-aks_service_name", required=False, default="dummycluster", type=str, help="AKS Service Name") 
    parser.add_argument("-aks_non_prod", required=False, default=False, type=bool, help="Indicates if the cluster is production level or not.") 
    
    # Attach
    parser.add_argument("-aks_existing_cluster", required=False, default=None, type=str, help="AKS VM node SKU") 
    parser.add_argument("-aks_existing_rg", required=False, default=None, type=str, help="AKS VM count in cluster") 

    # Create
    parser.add_argument("-aks_vm_size", required=False, default="Standard_D4_v2", type=str, help="AKS VM node SKU") 
    parser.add_argument("-aks_node_count", required=False, default=4, type=int, help="AKS VM count in cluster") 

    # Web Service Parameters
    parser.add_argument("-aks_num_replicas", required=False, default=2, type=int, help="AKS replica count of generated container.") 
    parser.add_argument("-aks_cpu_cores", required=False, default=1, type=int, help="Number of cores to allocate to each replica") 

    parsed_arguments = parser.parse_args(sys_args)

    '''
        For some reason, when loading from JSON and leaving None in the 
        input array for parser.parse_args, those values are getting turned 
        into the String None, correct that here.
    '''
    for attr, value in parsed_arguments.__dict__.items():
        if value == 'None':
            setattr(parsed_arguments, attr, None)


    return parsed_arguments    