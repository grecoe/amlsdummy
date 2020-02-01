import sys 
import argparse 
import pickle

def loadArguments(sys_args):
    # You prepare the parser the way you want it..... 
    parser = argparse.ArgumentParser(description='Simple model deployment.') 
    parser.add_argument("-subid", required=False, default='0ca618d2-22a8-413a-96d0-0f1b531129c3', type=str, help="Subscription ID") 
    parser.add_argument("-resourceGroup", required=False, default="dangtestbed", type=str, help="Resource Group") 
    parser.add_argument("-region", required=False, default="eastus", type=str, help="Azure Region") 
    parser.add_argument("-workspace", required=False, default="dangws", type=str, help="Workspace name") 
    parser.add_argument("-experiment", required=False, default="simple_experiment", type=str, help="Experiment name") 


    return parser.parse_args(sys_args)

def createPickle(file_name):
    '''
        Create a dummy pickle file
    '''
    my_data = {"nothing" : "to see here"}
    with open(file_name, 'wb') as model_file:
        pickle.dump(my_data, model_file)

