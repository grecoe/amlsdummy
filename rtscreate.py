'''
    Program Code: Create Azure Machine Learning Real Time Scoring Service

    Program will use settings from argument.py where user can optionally pass in parameters or 
    use the defaults set up. Those parameters and the user authentication are held in the Context class
    defined above. 

    Since this can be run in steps to slowly build up the service (as I did when creating this), each step
    validates if the object or service needs to be created. If it already exists (generally based on name)
    a new object/service is not created and the existing object/service is preserved in the Context class.

    Also note, each step needs to be performed in order (listed here) so that the appropriate objects/services
    are collected before trying to use them. 
'''
import os
import sys 
import json
from scripts.azure_utils import get_auth
from contexts.rtscontext import RealTimeScoringContext
from scripts.argument_utils import ExperimentType, loadConfiguration
from scripts.general_utils import JobType, JobLog

job_log = JobLog(JobType.real_time_scoring)

try:
    '''
        Get the program arguments and user authentication into the context
    '''
    job_log.startStep("Setup")
    programargs = loadConfiguration(ExperimentType.real_time_scoring,sys.argv[1:])
    userAuth = get_auth()
    program_context = RealTimeScoringContext(programargs, userAuth, job_log)
    job_log.endStep("Setup")


    '''
        Get or create an AMLS workspace. If the settings identify an existing 
        workspace, that workspace is retrieved. 
    '''
    job_log.startStep("Workspace")
    program_context.generateWorkspace()
    job_log.endStep("Workspace")

    '''
        Get or create an AMLS experiment. 
    '''
    job_log.startStep("Experiment")
    program_context.generateExperiment()
    job_log.endStep("Experiment")

  
    '''
        Get or create and AMLS model. 
    '''
    job_log.startStep("Model")
    program_context.generateModel()
    job_log.endStep("Model")

    '''
        Get or create (create could just update a registered container)
        a docker container image. This is then uploaded to the attached
        ACR instance.
    '''
    job_log.startStep("Container Image")
    if program_context.loadImage() == False:
        program_context.generateImage()
    job_log.endStep("Container Image")

    '''
        Get or create an AKS compute target.
        
        By providing a resource group and compute name, an existing
        cluster can be attached to the AMLS service. Otherwise a new cluster
        would be created and attached to the AMLS service. 
    '''
    job_log.startStep("Compute Target")
    program_context.generateComputeTarget(
         cluster_name = program_context.programArguments.aks_existing_cluster,
         resource_group = program_context.programArguments.aks_existing_rg
         )
    job_log.endStep("Compute Target")

    '''
        Get or create the web service that acts as the REST endpoint for this
        example. If creating, it creates a new service on the attached AKS cluster.
    '''
    job_log.startStep("Web Service")
    program_context.generateWebService()

    print(program_context.webserviceapi)
    if program_context.webserviceapi:
        for key in program_context.webserviceapi.keys():
            job_log.addInfo("{} - {}".format(key, program_context.webserviceapi[key] ))
    job_log.endStep("Web Service")

    '''
        Regardless of if we created or just retrieved an existin service, test it to 
        ensure it is responsive. 
    '''
    job_log.startStep("Web Service Test")
    program_context.testWebService()
    job_log.endStep("Web Service Test")

except Exception as ex:
    job_log.addInfo("An error occured executing this path")
    job_log.addInfo(str(ex))

job_log.dumpLog()

'''
    Clean up temporary files
'''
temp_files = ["simple.yml", "model.pkl", "scoring.py"]
for f in temp_files:
    if os.path.exists(f):
        os.remove(f)
