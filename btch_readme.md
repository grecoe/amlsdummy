# Batch Scoring Example
<sup> Daniel Grecoe - A Microsoft Employee</sup>

This code creates an Azure Machine Learning Batch Scoring service. The code in this repository can be run on Windows or Linux.

You will need
- A devlopment environment with anaconda installed. 
- Azure Subscription 
- Azure VM Machine Learning Cores for the batch scoring path. 
- Windows or Linux box to run the project

#### Prerequisites
1. Clone this repo to your machine
2. Create the conda environment
    - conda env create -f environment.yml
    - conda activate SimpleModel
3. Modify whatever settings you need. There are several ways to supply configuration for the main script, details are in the btchconfiguraiton.md file.  
4. Run the main script for your path - btchcreate.py with your chosen configuraiton to create the solution. 
5. When done, delete the resource group you identified in your choice of settings.

## Batch Scoring Repository Content
|Item|Type|Description|
|----|----|-----------|
|contexts|Directory|Contains implementations of Real Time Scoring and Batch Scoring models.|
|scripts|Directory|Contains utility scripts for loading configuration and making the actual Azure SDK calls.|
|environment.yml|File|Environment file to feed to conda to create the development environment to run this project.|
|btchconfiguration.md|File|Describes the different ways to provide configuration settings to the main batch scoring script (btchcreate.py)|
|btchconfiguration.json|File|Example configuration file as described in BTCHCONFIGURATION.md.|
|btchcreate.py|File|The main script that will perform all of the creation steps of the Azure Machine Learning workspace from resource group creation through to the deployment of an Azure Machine Learning Real batch scoring pipeline.|


<b>NOTE</b>: Re-running the code over and over will not produce anything outside of the original scope. At each step before any service, compute or pipeline is created, the Azure Machine Learning workspace is scanned for the item. If it exists, no new service is created. 


# Batch Scoring Scripts

## Script: btchcreate.py

## TBD