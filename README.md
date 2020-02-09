# Simple Cloud Machine Learning/AI Model Deployment using Azure
<sup> Daniel Grecoe - A Microsoft Employee</sup>

The code in this repository sets up different versions of an Azure Machine Learning Service. 

## Azure Machine Learning Real Time Scoring Service
For detailed information on the Azure Machine Learning Real Time Scoring Service deployed in this example read [this document]("./paths/realtime/rtsreadme.md").

A real time scoring service is a REST endpoint in which consumers of the endpoint send in individual records to be scored synchronously. Applications for such a service can be found in predicitive maintenance or other applications where some immediate action should occur. 

For example, a model is deployed for in a factory setting. At a given cadence the manufacturing equipement transmits it's current status and potentially the status over the last time period. 

The real time scoring service would then predict if the machine is about to experience some sort of issue. Business logic built with this endpoint could then shut down the machine or schedule a maintenance ticket. 

## Azure Machine Learning Batch Scoring Service
For detailed information on the Azure Machine Learning Batch Scoring Service deployed in this example read [this document]("./paths/batch/batchreadme.md").

A batch scoring service is an asynchronous service that can be run either on a schedule or when triggered. Applications for such a service can be found in financial services or other applications where periodic scoring of large numbers of records are required and immediate action is not neccesary. 

For example, certain fraudulent activity occurs over a period of time but is not detectable by individual transactions. Using a batch service, transaction historry would be collected by a back end system and placed in a storage area (many storage options are available for both input and outputs). 

When the input data is collected, the batch service would then be triggered to predict fraud over some period of records and output the results into another storage location for further business processing. 

## Repository Content

|Item|Type|Description|
|----|----|-----------|
|contexts|Directory|Source files that wrap Azure Functionality for both Batch and RealTime Scoring paths.|
|scripts|Directory|Utility source files  for dealing with program arguments, Azure services and logging.|
|paths|Directory|Detailed configuration information for both paths including scoring scripts to be utilized by the different paths.|
|environment.yml|File|File used to generate the required conda environment (see below)|
|batchcreate.py|File|Main script for deploying an Azure Machine Learning Batch Scoring service.|
|rtscreate.py|File|Main script for deploying an Azure Machine Learning Real Time Scoring service.|
|rtsloadtest.py|File|Script for load testing an Azure Machine Learning Real Time Scoring service.|
|LICENSE|File|MIT License for this repository.|
|README.md|File|The file you are reading now.|


## Common Configuration

### Conda Environment
Either path you choose you need to set up a conda environment to execute the scripts in as required Azure and Azure Machine Learning modules need to be present. 

1. Clone this repo to your machine
2. Create the conda environment
    - conda env create -f environment.yml
    - conda activate SimpleModel
3. Choose the path you want to follow:
    - Real Time Scoring - Navigate to  rtsreadme.md 
    - Batch Scoring - Navigate to batchreadme.md

### Logging
Regardless of path you execute, upon completion of either the rtscreate.py or batchcreate.py a log file directory is created with the following:

|Item|Type|Description|
|--|--|--|
|Logs|Directory|Holds all logs regardless of path executed.|
|Overview.csv|File|Generic CSV with three columns:<br><br>Path Type<br>Output Log File Name/Path<br>Execution Length in Seconds|
|BatchScoringLogs|Directory|Holds any log all  batchcreate.py runs. Each run creates it's own timestamped log file.|
|RealTimeScoringLogs|Directory|Holds any log all  rtscreate.py runs. Each run creates it's own timestamped log file.|