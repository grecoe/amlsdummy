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


'''
    Get the program arguments and user authentication into the context
'''
programargs = loadConfiguration(ExperimentType.batch_scoring,sys.argv[1:])
userAuth = get_auth()
program_context = BatchScoringContext(programargs, userAuth)


'''
    Get a workspace
'''
program_context.generateWorkspace()

'''
    Get or create batch compute
'''
program_context.generateCompute()
