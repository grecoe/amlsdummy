import pickle
import os
import json
from enum import Enum
from datetime import datetime, timedelta

class JobType(Enum):
    real_time_scoring = "RealTimeScoring"
    batch_scoring = "BatchScoring"

class JobLog:
    step_start = "start"
    step_end = "end"
    logs_directory = "Logs"
    general_stats = "Overview.csv"

    def __init__(self, jobtype):
        self.job_type = jobtype
        self.job_directory = jobtype.value + JobLog.logs_directory
        self.job_steps = {}
        self.job_info = {}
        self.total_start = None
        self.currentStep = None

    def lastStep(self):
        return self.currentStep
        
    def startStep(self, step_name):
        if len(self.job_steps) == 0:
            self.total_start = datetime.now()

        self.currentStep = step_name
        self.job_steps[step_name] = {}
        self.job_steps[step_name][JobLog.step_start] = datetime.now()

    def endStep(self, step_name):
        if step_name in self.job_steps.keys():
            self.job_steps[step_name][JobLog.step_end] = datetime.now()
    
    def addInfo(self, info):
        stamp = str(datetime.now())
        orig_stamp = stamp
        idx_counter = 1
        while stamp in self.job_info.keys():
            stamp = "{}({})".format(orig_stamp, idx_counter)
            idx_counter += 1

        self.job_info[stamp] = info

    def _dumpGeneral(self, log_path, total_time):

        if os.path.exists(JobLog.logs_directory) == False:
            os.makedirs(JobLog.logs_directory)

        stats_file = os.path.join(JobLog.logs_directory, JobLog.general_stats)
        log_entry = []
        log_entry.append(self.job_type.value)
        log_entry.append(log_path)
        log_entry.append(str(total_time))

        with open(stats_file, "a+") as general_stats:
            general_stats.writelines("{}\n".format(",".join(log_entry)))

    def dumpLog(self):

        total_run_time = datetime.now() - self.total_start

        log_path = os.path.join(JobLog.logs_directory, self.job_directory)
        if os.path.exists(log_path) == False:
            os.makedirs(log_path)
        
        file_name = datetime.now().isoformat()
        file_name = file_name.replace(":","-")
        file_name = file_name.replace(".","-")
        file_name += ".log"

        file_path = os.path.join(log_path, file_name)

        with open(file_path, "w") as log_output:
            log_object = {}
            log_object["type"] = self.job_type.value
            log_object["total_runtime"] = total_run_time.total_seconds()
            log_object["info"] = self.job_info
            log_object["steps"] = {}

            for step in self.job_steps.keys():
                time_delta = "Incomplete"
                if JobLog.step_start in self.job_steps[step].keys() and JobLog.step_end in self.job_steps[step].keys():
                    time_delt = self.job_steps[step][JobLog.step_end] - self.job_steps[step][JobLog.step_start]
                    time_delta = time_delt.total_seconds()
                
                log_object["steps"][step] = time_delta

            log_output.writelines(json.dumps(log_object, indent = 4))                


            '''
            log_output.writelines("Job Type: {}\n".format(self.job_type.value))
            log_output.writelines("Total Run Time: {} seconds\n".format(total_run_time.total_seconds()))
            log_output.writelines("Job Info: \n")
            for info in self.job_info:
                log_output.writelines("{} : {}\n".format(info["time"], info["info"]))

            log_output.writelines("Job Steps: \n")
            for step in self.job_steps.keys():
                if JobLog.step_start in self.job_steps[step].keys() and JobLog.step_end in self.job_steps[step].keys():
                    time_delt = self.job_steps[step][JobLog.step_end] - self.job_steps[step][JobLog.step_start]
                    log_output.writelines("    {} - {} seconds \n".format(step, time_delt.total_seconds()))
                else:
                    log_output.writelines("    {} - {} \n".format(step, self.job_steps[step]))
            '''

        self._dumpGeneral(file_path, total_run_time.total_seconds())


        



def createPickle(file_name):
    '''
        Create a dummy pickle file
    '''
    my_data = {"nothing" : "to see here"}
    with open(file_name, 'wb') as model_file:
        pickle.dump(my_data, model_file)

