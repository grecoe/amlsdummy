'''
    Program Code: Explores an experiment and will fail out any runs that 
                  have lasted longer than some pre-determined amount of time. 

    During some experimentation with customer managed keys, when the storage
    key is disabled an experiment will be created and a run started but it 
    throws an exception, I'm guessing because:

    - Experiments are stored in CosmosDB and that is succesful to create.
    - Run on experiment is started and also tagged in ComsosDB
    - Actual run needs storage on Azure ML workspace which is not available
      due to the key being revoked.
    - Exception is thrown and run will stay in running state indefinitely. 

    Program will use settings from argument.py where user can optionally pass in parameters or 
    use the defaults set up. Those parameters and the user authentication are held in the Context class
    defined above. 

    This program will NEVER create any resources, what MUST exist are

    - Azure ML Workspace
    - Experiment (by name)

    From there, all runs for the specified experiment will be stopped if they run
    longer than a pre-determined amount of time. 

    So, use this judiciously and only on experiments where you KNOW that it's hung.
    Don't accidentally kill runs that might be OK.
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
    continue_next_step = True

    '''
        Get the program arguments and user authentication into the context
    '''
    job_log.startStep("Setup")
    programargs = loadConfiguration(ExperimentType.real_time_scoring,sys.argv[1:])
    userAuth = get_auth()
    program_context = RealTimeScoringContext(programargs, userAuth, job_log)
    job_log.endStep("Setup")


    '''
        Get an existing workspace. If not succesful, no need to go further.
    '''
    job_log.startStep("Workspace")
    if not program_context.loadWorkspace():
        continue_next_step = False
        job_log.addInfo("Workspace does not exist.")
    job_log.endStep("Workspace")

    '''
        Get the existing image (that was used to create the service). 
        If not succesful no need to go further. 
    '''
    job_log.startStep("Experiment")
    if continue_next_step:
        try :
            program_context.getExistingExperiment()
        except Exception as ex:
            continue_next_step = False
            job_log.addInfo(str(ex))
    job_log.endStep("Experiment")

    job_log.startStep("Fail Long Runs")
    if continue_next_step:
        program_context.cancelExperimentLongRunningRuns(4)
    job_log.endStep("Fail Long Runs")

except Exception as ex:
    job_log.addInfo("An error occured executing this path")
    job_log.addInfo(str(ex))
    raise ex

job_log.dumpLog()

