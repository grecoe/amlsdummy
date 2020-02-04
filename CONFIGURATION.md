# Configuration
There are essentially three ways you can seed the required information to deploy this solution. 

1. Modify the parameters in scripts/general_utils.py in the loadArguments() function. 
    - These parameters are explicitly set to required=False. This means that you are not required to provide parameters on the command line if you do not wish to. 
2. Provide the neccesary parameters to the command line with expected types. 
3. Provide a configuration file in JSON format to the program and have the items parsed from there. An example configuration file is provided and is called configuration.json. 
    - To provide configuraiton file the only two arguments to the script are:
        - run.py -config [filename]
    - <b>NOTE</b>: The default configuraiton.json provided will NOT parse correctly because of the bool and int types that are expected.

## Subscription Level Settings
These settings are subscription level settings required to deploy the project.

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|subid|YES|String|Your Azure Subscription ID. This is the subscription that will be used throughout the scripts.|
|resourceGroup|YES|String|The name of an Azure Resource Group.<br><br>This can be an existing resource group or a new resource group to create.<br><br>To connect to an existing AMLS workspace, this must be an existing resource group.|
|region|YES|String|The Azure Region to deploy to (if creating new resources). For example: eastus|


## Azure Machine Learning Settings

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|workspace|YES|String|The name of an Azure Machine Learning workspace.<br><br>If connecting to an existing workspace, this name must exist in the resource group that is provided.<br><br>If not attaching to an existing workspace, a new Azure Machine Learning workspace will be created for you in the provided resource group.|
|experiment|YES|String|The name given to the Azure Machine Learning Experiment that will be created/loaded.|
|model_name|YES|String|The name given to the Azure Machine Learning Model that will be created/loaded.<br><br>This is not the name of the model file itself, just the registered model. The model file created for this exaple is model.pkl|
|image_name|YES|String|The name of the Docker Container image that will be created/loaded.|

## AKS Cluster Settings

### Common
|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|aks_compute_name|YES|String|The name given in Azure Machine Learning workspace to the compute being used. This is NOT the name of the actual AKS cluster that will be created/attached to.|
|aks_non_prod|YES|Bool|The value is either True/False or the string values "True"/"False".<br><br>Setting this to true, when a cluster is either created or attached the cluster purpose will be set to DEV_TEST. This allows you to create a cluster that is smaller than the size of a production cluster. For most cases, you will keep this value at False.|

    
### Create Cluster
These settings are ONLY required if you will be creating a new Azure Kubernetes Service (AKS) cluster. Otherwise the values can be set to None (json == null).

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|aks_vm_size|No|String|The SKU name for the Azure Virtual Machine type to be created for a NEW AKS cluster only.<br><br>Example: Standard_D4_v2|
|aks_node_count|No|Int|The number of Azure Virtual Machines to add to the AKS cluster when creating the cluster. This value is only useful for NEW AKS clusters.|

### Attach Cluster
These settings are ONLY required if you are attaching an exisitng Azure Kubernetes Service (AKS) cluster. 

If you are NOT attaching to an existing AKS cluster these values MUST be set to None (json == null)

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|aks_existing_cluster|NO|String|The name of an existing AKS cluster in your subscription to attach to.|
|aks_existing_rg|NO|String|The name of the Azure Resource Group containing the existing AKS cluster.|

## AKS Service Information
These settings are used when publishing the Web Service on the AKS cluster. 

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|aks_service_name|Yes|String|The name given to the Azure Machine Learning Web Service that will be created/loaded.|
|aks_num_replicas|No|Int|If creating a new web service this value IS required.<br><br>The number of containers to spin up on the AKS cluster to service the Real Time Scoring calls to the cluster.|
|aks_cpu_cores|No|Int|If creating a new web service this value IS required.<br><br>The number of CPU to assign to each container (aks_num_replicas) that will be spun up on the AKS cluster to service the Real Time Scoring calls to the cluster.|
