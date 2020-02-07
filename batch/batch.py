import sys
import os

# Passed in arguments
data_file = sys.argv[1]
data_directory = sys.argv[2]
output_file = sys.argv[3]
output_directory = sys.argv[4]


file_to_read = os.path.join(data_directory, data_file)
file_to_write = os.path.join(output_directory, output_file)

with open(file_to_read, "r") as input_file:
    with open(file_to_write, "w") as output_file:
        file_to_write.write(file_to_read.read())

