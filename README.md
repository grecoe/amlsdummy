# Simple Model
<sup> Daniel Grecoe - A Microsoft Employee</sup>

This code creates a simple Azure Machine Learning web service. 

The code can be run on Windows or Linux, but if run on Windows you cannot test the docker container image locally. That is the only restriction.

The project creates a no-op ML service that simply returns a string message to the user. That is, the ML model backing it is a NO-OP. It was created simply to go through all of the motions of creating a model, registering it, creating a container, creating an AKS compute cluster, and finally, deploying it as a REST endpoing. 

You will need
- Azure Subscription 
- Azure Machine Learning compute cores
- Windows or Linux box to run the project

NOTE: Re-running the code over and over will not produce anything outside of the original scope. At each step before the model, container image, aks service, or REST endpoint is created, the Azure Machine Learning workspace is scanned for the item. If it exists, no new service is created. 

Steps:
1. Clone this repo to your machine
2. Create the conda environment
    - conda env create -f environment.yml
    - conda activate SimpleModel
3. Modify whatever settings you need in
    - scripts\general_utils.py :: loadArguments()
    - Static class definitions in run.py :: class Context
4. Run run.py to create the solution
5. When done, delete the resource group identified in the program arguments
    - scripts\general_utils.py :: loadArguments()

