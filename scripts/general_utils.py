import sys 
import argparse 
import pickle
import os
import json

def _loadConfiguration(configuration_file):
    '''
        If the program is started with two arguments:
            -config [filename]
        
        The settings for the program will strictly be loaded from the configuration
        file, bypassing any other provided arguments AND the default settings in 
        loadArguments()
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
        return_settings.append(str(config_json[key]))
        
    return return_settings

def loadArguments(sys_args):
    '''
        Loads the arguments for the program. 
        User has the choice to:
        1. Provide no arguments -> Use defaults in this function
        2. -config [filename] as the only 2 arguments -> Load the settings from the configuration file
        3. Multiple arguments -> Use the provided arguments
    '''
    load_configuration = False
    if len(sys_args) == 0:
        print("Using default settings in loadArguments()")
    elif '-config' in sys_args and len(sys_args) == 2:
        print("Load configuration file for settings." , sys_args[1])
        sys_args = _loadConfiguration(sys_args[1])
    else:
        print("User provided settings will be used (along with any defaults not specified)")

    '''
        All of the parameters needed to execute a succesful deployment. These can simply be set here 
        so that you can run run.py without any additional parameters OR you can pass in one or many
        of the 13 settings.
    '''
    parser = argparse.ArgumentParser(description='Simple model deployment.') 

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

    return parser.parse_args(sys_args)

def createPickle(file_name):
    '''
        Create a dummy pickle file
    '''
    my_data = {"nothing" : "to see here"}
    with open(file_name, 'wb') as model_file:
        pickle.dump(my_data, model_file)

