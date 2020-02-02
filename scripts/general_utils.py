import sys 
import argparse 
import pickle

def loadArguments(sys_args):
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
            - AKS Compute name in AMLS Workspace
            - AKS Service name (the name of the generated webservice)
            - AKS Node SKU, the type of VM to create the cluster with
            - AKS Node count, the number of VM's to add to the cluster
            - AKS Replica count, number of instances of the container running in the cluster.
    ''' 
    parser.add_argument("-aks_name", required=False, default="dummyaks", type=str, help="AMLS Compute Name") 
    parser.add_argument("-aks_service_name", required=False, default="dummycluster", type=str, help="AKS Service Name") 
    parser.add_argument("-aks_vm_size", required=False, default="Standard_D4_v2", type=str, help="AKS VM node SKU") 
    parser.add_argument("-aks_node_count", required=False, default=4, type=int, help="AKS VM count in cluster") 
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

