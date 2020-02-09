'''
    Program Code: Create Azure Machine Learning BATCH Scoring Service

    
    NOTE: THIS PATH IS INCOMPLETE
'''

import os
import sys 
import json
from scripts.azure_utils import get_auth
from contexts.btchcontext import BatchScoringContext
from scripts.argument_utils import ExperimentType, loadConfiguration
from scripts.general_utils import JobType, JobLog


job_log = JobLog(JobType.batch_scoring)

try :
    '''
        Get the program arguments and user authentication into the context
    '''
    job_log.startStep("Setup")
    programargs = loadConfiguration(ExperimentType.batch_scoring,sys.argv[1:])
    userAuth = get_auth()
    program_context = BatchScoringContext(programargs, userAuth)
    job_log.endStep("Setup")


    '''
        Get or create an AMLS workspace. If the settings identify an existing 
        workspace, that workspace is retrieved. 
    '''
    job_log.startStep("Workspace")
    program_context.generateWorkspace()
    job_log.endStep("Workspace")


    '''
        Because this example is using Azure Storage for both input and output
        we need to ensure that the containers in the storage account exists. 
    '''
    job_log.startStep("Storage Containers")
    program_context.generateStorageContainers()
    job_log.endStep("Storage Containers")

    '''
        Upload the data file that will be processed by the batch service. In a real
        service this file would just be a pointer to data we expect to be there and 
        not a full file on it's own. 
    '''
    job_log.startStep("File Uploads")
    program_context.uploadDataFiles()
    job_log.endStep("File Uploads")

    '''
        Get or create batch compute. Batch compute is managed by AMLS itself. The 
        nodes are brought online when a batch service starts. 
    '''
    job_log.startStep("Batch Compute")
    program_context.generateCompute()
    job_log.endStep("Batch Compute")

    '''
        Create the datasets that the pipeline requires. Two are created, one for 
        input and one for output. 
    '''
    job_log.startStep("Data References")
    program_context.createPipelineDataReferences()
    job_log.endStep("Data References")

    '''
        Create the pipeline that will process data in a batch state. Internally, 
        the pipeline will be scheduled to run every hour. 
    '''
    job_log.startStep("Pipeline Creation")
    program_context.createPipeline()
    job_log.endStep("Pipeline Creation")


    '''
        Add in final details and dump the log
    '''
    job_log.addInfo("Pipeline Status: {}".format(program_context.publishedPipeline.status))
    job_log.addInfo("Pipeline Endpoint: {}".format(program_context.publishedPipeline.endpoint))
    
except Exception as ex:
    job_log.addInfo("An error occured executing this path")
    job_log.addInfo(str(ex))

job_log.dumpLog()