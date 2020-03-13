import platform
import datetime
from scripts.azure_utils import setContext
from azureml.core.image import ContainerImage
from scripts.azure_utils import *

class BaseContext:

    '''
        Contains base context items
    '''
    def __init__(self, programArgs, userAuthorization, job_log = None):
        self.programArguments = programArgs
        self.authentication = userAuthorization
        self.platform = platform.system().lower()
        self.workspace = None
        self.experiment = None
        self.model = None
        self.job_log = job_log

        if not self.authentication:
            raise Exception("Authentication object missing")

        '''
            Change the context to the provided subscription id
            This expects that an az login has already occured with a user
            that has the correct credentials.
        '''
        setContext(self.programArguments.subid)

    def loadWorkspace(self):
        '''
            Used to only retrieve an existing workspace.
        '''
        self.workspace = getExistingWorkspace(
            self.authentication, 
            self.programArguments.subid, 
            self.programArguments.resourceGroup,
            self.programArguments.workspace,
            self.job_log
            )

        return self.workspace != None

    def generateWorkspace(self):
        '''
            Gets an existing workspace (by name) or creates a new one

            retrieve_only - If true, worksapce will NOT be created but only
                            retrieved. 
        '''
        
        self.workspace = getOrCreateWorkspace(
            self.authentication, 
            self.programArguments.subid, 
            self.programArguments.resourceGroup,
            self.programArguments.workspace,
            self.programArguments.region,
            self.job_log
            )

        if not self.workspace:
            raise Exception("Workspace Creation Failed")

    def generateExperiment(self):
        '''
            Get an existing experiment by name, or create new
        '''
        self.experiment = getOrCreateExperiment(self.workspace, self.programArguments.experiment, self.job_log)

        if not self.experiment:
            raise Exception("Experiment Creation Failed")

    def getExistingExperiment(self):
        '''
            Get an existing experiment by name, or create new
        '''
        self.experiment = getExistingExperiment(self.workspace, self.programArguments.experiment, self.job_log)

        if not self.experiment:
            raise Exception("Experiment Collection Failed")

    def cancelExperimentLongRunningRuns(self, hours):

        if not self.experiment:
            raise Exception("Must have an experiment to get runs")
        
        run_list = self.experiment.get_runs()
        for run in run_list:
            details = run.get_details()

            print("Checking run ", details['runId'])
            
            start_str = details['startTimeUtc']
            time_start = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            time_now = datetime.datetime.utcnow()
            
            if not 'endTimeUtc' in details.keys():
                cancel = True
                hours_diff = None
                print("Run still going....")
                if 'startTimeUtc' in details.keys():
                    start_str = details['startTimeUtc']
                    time_start = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    time_now = datetime.datetime.utcnow()
                    time_diff = time_now - time_start
                    seconds_diff = time_diff.seconds
                    
                    if time_diff.days > 0:
                        seconds_diff += time_diff.days * 86400
                    
                    hours_diff = seconds_diff / 3600
                    if hours_diff < hours:
                        cancel = False

                if cancel:
                    str_message = "Run {} going for {} hours marked failed.".format(details['runId'], hours_diff)
                    print(str_message)
                    run.fail(error_details = str_message)
