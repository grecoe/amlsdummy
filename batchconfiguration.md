# Configuration - Batch Scoring
<sup> Daniel Grecoe - A Microsoft Employee</sup>


There are essentially three ways you can seed the required information to deploy this solution. 

1. Modify the parameters in scripts/argument_utils.py in the _loadBatchArguments() function. 
    - These parameters are explicitly set to required=False. This means that you are not required to provide parameters on the command line if you do not wish to. 
2. Provide the neccesary parameters to the command line with expected types. 
3. Provide a configuration file in JSON format to the program and have the items parsed from there. An example configuration file is provided and is called rtsconfiguration.json. 
    - To provide configuraiton file the only two arguments to the script are:
        - batchcreate.py -config [filename]
    - <b>NOTE</b>: The default batchconfiguraiton.json provided will NOT parse correctly because of the bool and int types that are expected.

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

## Batch Compute Cluster Settings

|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|batch_compute_name|YES|String|The name given in Azure Machine Learning workspace to the compute being used. This is NOT the name of the actual AKS cluster that will be created/attached to.|
|batch_vm_size|No|String|The SKU name for the Azure Virtual Machine type to be created for a NEW Batch cluster only.<br><br>Example: Standard_D2|
|batch_vm_max|No|Int|The maximum number of Azure Virtual Machines to add to the cluster when creating the cluster. This value is only useful for NEW AML Compute clusters.|
|batch_vm_min|No|Int|The minimum number of Azure Virtual Machines to leave running.  This value is only useful for NEW AML Compute clusters.|

## Pipeline Settings

### General
|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|pipeline_name|Yes|AMLS Pipeline name.|
|batch_script_folder|Yes|Local folder holding batch script|
|batch_script|Yes|Pyhon file to run on batch cluster.|
|source_container|Yes| Azure Storage container for source data files.|
|result_container|Yes|Azure Storage container for results data file.|
|data_folder|Yes|String|Local directory holding data files.|
|data_files|Yes|String|Comma separated list of files to upload to source_container that exist in data_folder|
|result_file|Yes|String|File name for output of batch result.|

### Schedule
|Property|Required|Type|Description|
|--------|--------|-----|-----------|
|schedule_frequency|Yes|String|Frequency that the scheduled pipeline runs.|
|schedule_interval|Yes|Int|The interval of schedule_frequency to run the scheduled pipeline.|

