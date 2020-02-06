from scripts.azure_utils import *
from contexts.basecontext import BaseContext

class BatchScoringContext(BaseContext):

    '''
        Contains the context needed to perform the tasks. 
    '''
    def __init__(self, programArgs, userAuthorization):
        super().__init__(programArgs, userAuthorization)
        self.computeTarget = None
        self.computeTarget = None

    def generateCompute(self):

        if self.computeTarget:
            return self.computeTarget

        self.computeTarget = createBatchComputeCluster(
            self.workspace,
            self.programArguments.batch_compute_name,
            self.programArguments.batch_vm_size,
            self.programArguments.batch_vm_max,
            self.programArguments.batch_vm_min
        )
        
        if not self.computeTarget:
            raise Exception("Cannot create compute target.")
