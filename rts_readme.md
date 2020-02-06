# Real Time Scoring Example
<sup> Daniel Grecoe - A Microsoft Employee</sup>

This code creates an Azure Machine Learning Real Time Scoring service. The code in this repository can be run on Windows or Linux. The only restriction with Windows is that you cannot test the docker container image locally on the real time scoring path. 

The project creates a no-op Machine Learning WebService that simply returns a string message to the user. That is, the ML model backing it is a NO-OP. It was created simply to go through all of the motions of creating a model, registering it, creating a container, creating an AKS compute cluster, and finally, deploying it as a REST endpoint. 

You will need
- A devlopment environment with anaconda installed. 
- Azure Subscription 
- Azure VM Cores (Standard DSv2, and at least 24) available in the region you choose for deployment for the real time scoring path.
- Windows or Linux box to run the project
    - If running on Windows you will not be able to test the docker container locally as the image is Linux based. However, you'll still be able to create and deploy a service.

#### Prerequisites
1. Clone this repo to your machine
2. Create the conda environment
    - conda env create -f environment.yml
    - conda activate SimpleModel
3. Modify whatever settings you need. There are several ways to supply configuration for the main script, details are in the rtsconfiguraiton.md file. . 
4. Run the main script for your path - rtscreate.py with your chosen configuraiton to create the solution..
5. When done, delete the resource group you identified in your choice of settings.

## Real Time Scoring Repository Content
|Item|Type|Description|
|----|----|-----------|
|contexts|Directory|Contains implementations of Real Time Scoring and Batch Scoring models.|
|scripts|Directory|Contains utility scripts for loading configuration and making the actual Azure SDK calls.|
|environment.yml|File|Environment file to feed to conda to create the development environment to run this project.|
|rtsconfiguration.md|File|Describes the different ways to provide configuration settings to the main script real time scoring (rtscreate.py)|
|rtsconfiguration.json|File|Example configuration file as described in CONFIGURATION.md.|
|rtscreate.py|File|The main script that will perform all of the creation steps of the Azure Machine Learning workspace from resource group creation through to the deployment of an Azure Machine Learning Real Time Scoring service.|
|scoring.py|File|This file is used when creating the Azure Machine Learning Real Time Scoring service and does not need altering in any way.|
|rtsloadtest.py|file|Secondary script to test your public Azure Machine Learning Real Time Scoring service in a load test type of way.|


### Linux only 
To test the container image you have to perform the following commands from the bash shell.

```
sudo usermod -aG docker $USER
newgrp docker
```

<b>NOTE</b>: Re-running the code over and over will not produce anything outside of the original scope. At each step before the model, container image, aks service, or REST endpoint is created, the Azure Machine Learning workspace is scanned for the item. If it exists, no new service is created. 

### Real Time Scoring - Deployed API Input/Return
This example produces a REST API with the expected input:

|||
|----|----|
|ACTION|POST|
|URL| URL of the web service|
|API KEY| As bearer token in request headers <br> EX: Authorization : Bearer KEY|
|CONTENT-TYPE|application/json|
|BODY|Simple JSON body:
```
{
    "name" : "Any name or string"
}
```

The API returns a simple JSON structure in the form:
```
{
    "GoAway" : "[name]'s not here."
}
```
Where [name] is the input value. 

Service code that generates the response is in scoring.py.

# Real Time Scoring Scripts

## Script: rtscreate.py
This is the main Python script to create everythign from the resource group -> REST endpoint. 

It uses configuration parameters (as noted above) as to where to create the Azure services as well as any other configuration settings that can be used. 

Configuration parameters can be provided in several ways, read CONFIGURATION.md to determine the best way to provide parameters for your needs. 

Further, it utilizes the scoring.py file as the script that sits behind the REST endpoint. 

1. Create the context object
2. Generate an Azure Machine Learning Service Workspace
    - If workspace already exists by name in the sub with the provided resource group, that workspace it will be added to the Context object. 
    - If it doesn't exist it is created and added to the Context object.
3. Generate the AMLS Experiment
    - If the experiment exists in the workspace by name, it will be added to the Context object.
    - If the experiment doesn't exist it is created and added to the Context object..
4. Create a model
    -This is really a no-op model. A pkl file is generated from nothing useful, but the model file is required to create a container.
    - If the model already exists by name it will be added to the Context object
    - If it doesn't exist, a simple pkl file is generated and registered as a new model. The result is added to the Context object.
5. Create a conatiner image. 
    - Attempts to load a container image associated with the current workspace. 
        - If found, it is added to the Context object
        - If not found, creates a new container image and adds it to the Context object.
            - It is ok to just create new images, it just updates the version in the ACR
            - Once the image is created, attempts to test the container image locally. However this is a Linux based image so if the current system is not Linux test will not run. 
6. Creates or attaches a compute target (in this case AKS)
    - If you have a cluster alreayd, use the function Context.generateComputeTarget by supplying the cluster name and resource group. The existing cluster is then added to the Context object.
    - If you need a new cluster, leave those fields blank and:
        - If a compute with the same name is already associated with the workspace, that compute is added to the Context object.
        - If a compute doesn't exist, it is created and added to the Context object.
7. Create the web service to serve up the REST api endpoint.
    - If a service already exists in the workspace for the expected container image name, that service is added to the Context object.
    - If the service doessn't exist, a new one is created and added to the Context object.
8. The web service is tested and the result is printed to the console along with the connection info for the service, i.e. URI and KEY. When this succeeds, you can take that connection info and use it elsewhere. 
    - If you don't record the API information, you can simply re-run this script and it will be collected for you without creating any new objects/resources (assuming you have not changed the configuration)

## Script: rtsloatest.py 
Once the endpoint has been published with rtscreate.py you should have the API URL and KEY printed out to the console. 

Use these values to then call the rtsloadtest.py file and load test your endpoint. 

You pass in parameters to this file to have it execute the endpoint you just published with rtscreate.py. 

The script is actually fairly flexible and with minor changes for payload, you could use this script against almost any endpoint. 

### rtsloadtest.py Parameters
|||
|---|---|
|u|Web service URL|
|k|Web service API Key|
|t|Number of threads to spawn.|
|i|Number of calls (iterations) that each thread should make before returning.|
