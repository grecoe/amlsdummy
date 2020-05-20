'''
    After deploying your Web Service, you can use this program to load test the endpoint. 

    Read the function loadArguments() to determine what parameters to pass in. 

    Flow:
        1. Create and start t number of threads where t is identified in the parameters.
            Each thread will run for i iterations (calls to the endpoint) where i is identified
            in the parameters.
        2. Upon completion of all threads collect statistics.
            - All up stats on all calls from all threads
            - Individual thread statistics
            - Each stats bundle contains
                Total Number of Calls
                Succesful Number of Calls
                Average Latency (seconds)
                Min Latency (seconds)
                Max Latency (seconds)
        3. Print the results to the console. 
'''

from threading import * 
from datetime import datetime, timedelta 
import sys 
import argparse 
import time 
import requests
import json
import collections
import random
import statistics

# Named tuple to collect from each call
test_point = collections.namedtuple('test_point', 'thread status elapsed')
# Collection of each call made
test_collection = []
# Global lock to protect collection
test_collection_lock = RLock()

# Counter of running threads
running_threads = 0

# Headers for every call
api_headers = {}


def loadArguments(sys_args):
    '''
        Load arguments for the program:

        u = URL of the Web Service URL
        k = API Key for the web service
        t = Number of threads to run
        i = Number of calls to make per thread. 
    '''
    global api_headers

    parser = argparse.ArgumentParser(description='Simple model deployment.') 
    parser.add_argument("-u", required=False, default='http://40.121.6.20:80/api/v1/service/dummycluster/score', type=str, help="Web Service URI") 
    parser.add_argument("-k", required=False, default="eGKplWLsq0AKDFx8gb5SyaKU8AeoDqOc", type=str, help="Web Service Key") 
    parser.add_argument("-t", required=False, default=20, type=int, help="Thread Count") 
    parser.add_argument("-i", required=False, default=1, type=int, help="Thread Iterations") 

    prog_args = parser.parse_args(sys_args)

    api_headers["Authorization"] = "Bearer " + prog_args.k
    api_headers["Content-Type"] = "application/json"

    return prog_args

def dumpStats(stats):
    '''
        Dump out a dictionary of stats 
    '''
    for key in stats.keys():
        print("    ", key, "=", stats[key])

def getStatistics(collection):
    '''
        From a collection of test_point objects collect the following
        - T0tal Calls
        - Succesful calls
        - Average latency
        - Min latency
        - Maximum Latency
    '''
    stats = {}

    success = [x for x in collection if x.status == 200]
    times = [x.elapsed for x in collection ]

    stats["calls"] = len(collection)
    stats["success"] = len(success)
    stats["average"] = statistics.mean(times)
    stats["min"] = min(times)
    stats["max"] = max(times)

    return stats

def getThreadStatistics():
    '''
        Load statistics of the run. Two items are returned as a list

        [0] = Dictionary of global stats
        [1] = Dictionary of dictionaries for each thread. 
    '''
    global test_collection

    '''
        Get stats across threads
    '''
    global_stats = getStatistics(test_collection)

    '''
        Get individual stats
    '''
    thread_stats = {}
    thread_ids = [x.thread for x in test_collection]
    thread_ids = list(set(thread_ids))
    for tid in thread_ids:
        thread_stats[tid] = {}
        thread_collection = [x for x in test_collection if x.thread == tid]
        thread_stats[tid] = getStatistics(thread_collection)

    return [global_stats, thread_stats]

class ThreadRun(Thread): 
    '''
        Class used as a thread to run the load test against the 
        endpoint. 
    '''
 
    def __init__(self, id, iterations, url, headers, payload): 
        Thread.__init__(self) 
        self.id = id 
        self.iterations = iterations
        self.url = url
        self.headers = headers
        self.payload = payload

    '''
        Calling start() runs this as well, but when you queue a thread it will 
        trigger this as well. 
    '''
    def run(self):
        global running_threads
        global test_collection
        global test_collection_lock

        print("Staring thread", self.id)
        for i in range(self.iterations):
            try:
                response = requests.post(url = self.url, headers = self.headers, data = json.dumps(self.payload))
                current_test = test_point( self.id, response.status_code, response.elapsed.total_seconds())
            except Exception as ex:
                print(self.id, ex)
                print(str(ex))
                current_test = test_point( self.id, 500, 1)


            test_collection_lock.acquire()
            test_collection.append(current_test)
            test_collection_lock.release()

        test_collection_lock.acquire()
        running_threads -= 1
        test_collection_lock.release()


'''
    Program Code:

    The configured number of threads will be executed for the configured number of iterations each 
    hitting the endpoint. 

    This can be used for any number of AMLS endpoints, with the real change being to the payload that is set 
    into the thread class to perform the execution. 
'''


'''
    Using the configuration, fire up as many threads as we need. 
'''
configuration = loadArguments(sys.argv[1:])   
names = ["Dave", "Sue", "Dan", "Joe", "Beth"]

# Capture the start time.
start_time = datetime.now()

for i in range(configuration.t):
    payload = {'name' : names[random.randint(0, len(names) -1)]}
    run = ThreadRun(i+1, configuration.i, configuration.u, api_headers, payload)
    
    # Increase the thread counter
    test_collection_lock.acquire()
    running_threads += 1
    test_collection_lock.release()
    
    # Start the worker thread.
    run.start()

'''
    Wait until all threads complete.
'''
counter = 0
while running_threads > 0:
    counter += 1
    if counter %3 == 0:
        print("Waiting on threads, current count =", running_threads)
    time.sleep(.5)

# Capture the start time.
end_time = datetime.now()
total_seconds = (end_time - start_time).total_seconds()
print(total_seconds)

'''
    Get and print out the statistics for this run. 
'''
stats = getThreadStatistics()
print("Global Stats:")
print("     Total Time  : ", total_seconds )
print("     Overall RPS : ", stats[0]["calls"] / total_seconds )
dumpStats(stats[0])
for thread_id in stats[1].keys():
    print("Thread", thread_id, "Stats:")
    dumpStats(stats[1][thread_id])

