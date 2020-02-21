import platform
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


