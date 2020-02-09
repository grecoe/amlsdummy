import sys
import os

'''
    Arguments set up for the pipeline to be passed along. 

    These are set in /contexts/btchcontext.py when creating the PythonScriptStep on or around
    line 173. 

    Because you identify what these are, it would be a good idea to also pass flags along so
    you could use argparse to parse out the values instead of having to know the exact order 
    of arguments like this example does.
'''
data_file = sys.argv[1]
data_directory = sys.argv[2]
output_file = sys.argv[3]
output_directory = sys.argv[4]

'''
    The data directory identifies where the data is for the process to read. This is created
    for you when the process is launched. The output directory, however, is just identified 
    in the argument but the system does NOT create that on your behalf. 
'''
file_to_read = data_directory + '/' +  data_file
file_to_write = output_directory + '/' + output_file

''' 
    Create the output directory and the results file that was identified (and expected).
'''
os.makedirs(output_directory)

with open(file_to_write, "w") as output_file:
    output_file.write(file_to_read + "\n")
    output_file.write(file_to_write + "\n")

