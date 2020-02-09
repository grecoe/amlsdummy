# Batch Scoring Example
<sup> Daniel Grecoe - A Microsoft Employee</sup>

This code creates an Azure Machine Learning Batch Scoring service into your Azure subscription. 

The code in this repository can be run on Windows or Linux with no restrictions as the docker container image is not tested locally.

The batch scoring service deployed will utilize Azure Storage for both input and output sources to the batch model. The Azure Storage account used is the one that is created by the Azure Machine Learning service.

The deployed scoring script does not utilize any actual Machine Learing/AI models but simply prints out information to the output to show that it did, in fact, run. 

The purpose of this example is to exhibit the steps and services neccesary for deploying an Azure Machine Learning Batch Service in your subscripiton only. No actual data science and model building are performed in this example. 

You will need
- A devlopment environment with anaconda installed. 
- Azure Subscription 
- Azure VM Machine Learning Cores for the batch scoring path. 
- Windows or Linux box to run the project

#### Prerequisites
1. Ensure you have activated the conda environment SimpleModel. 
2. Modify whatever settings you need. There are several ways to supply configuration for the main script, details are in the batchconfiguraiton.md file.  
3. Run the main script for your path - batchcreate.py with your chosen configuraiton to create the solution. 
5. When done, delete the resource group you identified in your choice of settings.

## Azure Service Creation
During the creation of this solution the following Azure Services are created in your subscription:

|Service|Purpose|
|-------|--------|
|Azure Resource Group| The Azure Resource group is a container that will hold other Azure resources.<br><br>For this project there will actually be two resource groups created. The first for the Azure Machine Learning required services, and the second for the Azure Kubernetes Service cluster nodes.|
|Azure Machine Learning|This is the main machine learning service and orchestrates communication and data movement amongst other Azure services.<br><br>Further, the actual compute nodes used to service the calls to the resulting batch endpoint are associated with this service. This is different from the RTS path which utilizes Azure Kubernetes Service. |
|Azure Container Registry| The project creates Docker containers which are then stored in the ACR|
|Azure Key Vault|The key vault is used to store secrets for the solution such as passwords to the ACR and connection strings to the storae account.|
|Azure Storage Account|This storage is used extensively with the AMLS service storing code snapshots, other outputs and logs.|
|Application Insights|Application insights is used to capture metrics and other data related to a published model/endpoint.|

## Batch Scoring Repository Content
The main source files for this project are described in the master README.MD file in the respository. 

Repository content described there is not duplicated here. 

This table describes only what is in this directory.

|Item|Type|Description|
|----|----|-----------|
|scoring|Directory|Contains two files that are used when deploying the service :<br><br>- data.txt : The mock input file to the batch scoring service. <br><br>- batch.py : The source file behind the actual bach scoring process.| 
|batchconfiguration.md|File|Describes the different ways to provide configuration settings to the main batch scoring script (batchcreate.py)|
|batchconfiguration.json|File|Example configuration file as described in batchconfiguration.md.|
|batchreadme.md|File|The file you are reading now.|


<b>NOTE</b>: Re-running the code over and over will not produce anything outside of the original scope. At each step before any service, compute or pipeline is created, the Azure Machine Learning workspace is scanned for the item. If it exists, no new service is created. 


# Batch Scoring Scripts
These scripts are found in at the head of the master repository, but details of how they perform the actions neccesary are described here.

## Script: batchcreate.py

This is the main Python script to create everythign from the resource group -> REST endpoint to batch service.

It uses configuration parameters (as noted above) as to where to create the Azure services as well as any other configuration settings that can be used. 

Configuration parameters can be provided in several ways, read batchconfiguration.md to determine the best way to provide parameters for your needs. 

Further, it utilizes the batch/batch.py file as the script that sits behind the REST endpoint to be executed on each of the batch nodes, and batch/data.txt as the file to process during the batch call. 

1. Create the context object
2. Generate an Azure Machine Learning Service Workspace
    - If workspace already exists by name in the sub with the provided resource group, that workspace it will be added to the Context object. 
    - If it doesn't exist it is created and added to the Context object.
3. Generate neccesary Azure Storage Containers
    - If a container does not exist, it is created at run time. 
4. Creates or attaches a compute target (in this case AML Batch Compute)
    - Unlike AKS you cannot attach an existing compute resource.**
    - If a compute with the same name is already associated with the workspace, that compute is added to the Context object.
        - If a compute doesn't exist, it is created and added to the Context object.
5. Create Data References. Data references are used to tell the batch jobs where data/models/etc are coming from and where results should be written to. Data References are generated from Data Store objects. 
    - If an associated data store does not exist, create it. 
    - Wrap data store with Data Reference objects for both input (1 input) and output (1 output).
6. Create the AMLS Pipeline. 
    - If a Pipeline with the same name already exists, no changes are made to the service. Otherwise, create a new Pipeline and register it with the AMLS service. 
