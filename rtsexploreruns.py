'''
    Program Code: Delete an RTS Webservice instance from a workspace.

    Program will use settings from argument.py where user can optionally pass in parameters or 
    use the defaults set up. Those parameters and the user authentication are held in the Context class
    defined above. 

    This script will NEVER create any resources. The only side effect is that
    a web service will be deleted, if found. 
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

