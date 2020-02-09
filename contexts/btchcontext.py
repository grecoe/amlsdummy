import os
from scripts.azure_utils import *
from contexts.basecontext import BaseContext

from azureml.core.runconfig import CondaDependencies, RunConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline, PipelineData, PublishedPipeline
from azureml.pipeline.core.schedule import ScheduleRecurrence, Schedule

class BatchScoringContext(BaseContext):
    # Data and script information
    batch_data_directory = './paths/batch/scoring'
    batch_data_file = 'data.txt'
    batch_scoring_script = 'batch.py'
    bach_scoring_results_file = "Results.txt"

    # Data store information
    input_store_name = "inputdata"
    input_reference_name = "inputdataref"
    output_store_name = "outputdata"
    output_reference_name = "outputdataref"

    # Pipeline information
    pip_packages = []
    python_version = "3.6.7"

    '''
        Contains the context needed to perform the tasks. 
    '''
    def __init__(self, programArgs, userAuthorization):
        super().__init__(programArgs, userAuthorization)
        self.computeTarget = None
        self.inputDataStore = None
        self.inputDataReference = None
        self.outputDataStore = None
        self.outputDataReference = None
        self.pipelineStep = None
        self.pipeLine = None
        self.publishedPipeline = None
        
    def generateStorageContainers(self):
        '''
            We are using the storage associated with the actual AMLS workspace. 

            So, we need to create the container that has the data to be "scored" and 
            a container where results will end up. 
        '''
        storage_container_names = []
        storage_container_names.append(self.programArguments.source_container)
        storage_container_names.append(self.programArguments.result_container)

        storage_details = self.workspace.get_default_datastore()

        createStorageContainer(
            storage_details.account_name,
            storage_details.account_key,
            storage_container_names)

    def uploadDataFiles(self):
        '''
            Upload the data files into the source container, these are the 
            files that will be processed by the AML compute cluster.
        '''
        storage_details = self.workspace.get_default_datastore()
        data_files = BatchScoringContext.batch_data_file.split(",")

        uploadStorageBlobs(
            storage_details.account_name,
            storage_details.account_key,
            self.programArguments.source_container,
            BatchScoringContext.batch_data_directory,
            data_files)

    def generateCompute(self):
        '''
            Generate the AML compute cluster. 
        '''
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

    def createPipelineDataReferences(self):
        '''
            Datastores identify where data is coming from and going to in the process. This 
            function checks to see if a data store with the same name has already been registered.

            If not, it registers it, if so it uses the exsiting store.

            Stores are then wrapped in a DataReference object that will be used in the pipeline steps. 

            For this example, we need two references. One for the input data file, one for the output results file. 
            Both reside in the storage account from the AMLS workspace.
        '''

        storage_details = self.workspace.get_default_datastore()

        '''
            Have to create one for input and one for output. 
            self.programArguments.source_container - identifies the container name for the data file
            self.programArguments.result_container - identifies the container name for the results file(s)
        '''
        requested_datasets = {}

        requested_datasets["in"] = (
                 self.programArguments.source_container,
                 BatchScoringContext.input_store_name,
                 BatchScoringContext.input_reference_name 
                 )
        requested_datasets["out"] = (
                 self.programArguments.result_container,
                 BatchScoringContext.output_store_name,
                 BatchScoringContext.output_reference_name
                  )

        for requested in requested_datasets:
            store, reference = createDataReference(
                            self.workspace,
                            storage_details.account_name,
                            storage_details.account_key,
                            requested_datasets[requested][0],
                            requested_datasets[requested][1],
                            requested_datasets[requested][2]
                        )

            '''
                Put the reference into the class variables. 
            '''
            if requested == "in":
                self.inputDataStore = store
                self.inputDataReference = reference
            else:
                self.outputDataStore = store
                self.outputDataReference = reference
      
    def _createPipelineSteps(self):

        '''
            You first need the conda dependencies that will be baked into the image to 
            be pushed down to the batch compute cluster for a working environment.

            In this example we don't need anything other than Python.
        '''
        conda_dependencies = CondaDependencies.create(
                pip_packages=BatchScoringContext.pip_packages, python_version=BatchScoringContext.python_version
                )
        
        run_config = RunConfiguration(conda_dependencies=conda_dependencies)
        run_config.environment.docker.enabled = True

        '''
            Next we need to let the pipeline know which store the output is going. This is expected
            to be a PipelineData object. That object expects:

            name = The directory on the cluster machine in which output is expected.
            datastore = Identifies the end storage. In this case an Azure Storage account complete with 
                        container name and file name in which to deposit in the storage account. 
        '''
        prediction_ref = PipelineData(name="preds", datastore=self.outputDataStore, is_directory=True)
        '''
            Next we create a step for a pipeline. 

            WE tell it where out script is, 
                Script information:
                    The directory in which the python script is located on the local machine
                    The file name of the script that will be uploaded.
                Script Arguments:
                    This is what arguments the script will accept. In our example they are:
                        input file, input directory, output file, output directory
                inputs: 
                    This is a list of data inputs. In this example it is the Azure Storage account/container/file
                    combination that holds our data file.  
                outputs: 
                    This is a list of outputs. In this example it is the Azure Storage account/container/file 
                    combination that the script creates.  
                compute_target:
                    The compute target we attached to the AML service that will process requests. 
                run_config: 
                    This is the conda / python depenencies that the resultant container requires to execute succesfully. 
        '''
        self.pipelineStep = PythonScriptStep(
            name="basic_pipeline_step",
            source_directory = BatchScoringContext.batch_data_directory,
            script_name = BatchScoringContext.batch_scoring_script,
            arguments = [ BatchScoringContext.batch_data_file, self.inputDataReference, BatchScoringContext.bach_scoring_results_file , prediction_ref],
            inputs = [self.inputDataReference],
            outputs = [prediction_ref],
            compute_target = self.computeTarget,
            runconfig = run_config,
            allow_reuse=False,
        )     

        if self.pipelineStep == None:
            raise Exception("Unable to create python step.")               


    def createPipeline(self):
        '''
            A pipeline is a series of steps but also requires DataReference objects in those steps so 
            that it where to get data from and where to deposit outputs. 

            In this step, if a PublishedPipeline exists by name, a new pipeline is not created. 

            If it is created a new docker conainer is generated in the ACR instance associated with this 
            AMLS workspace. 
        '''
        self.publishedPipeline = getExistingPipeline(self.workspace, self.programArguments.pipeline_name)

        if self.publishedPipeline :
            print("Found existing pipeline - ", self.programArguments.pipeline_name)
        else:
            print("Creating  pipeline - ", self.programArguments.pipeline_name)

            print("Creating pipeline steps .....")
            self._createPipelineSteps()
            self.pipeLine = Pipeline(workspace= self.workspace, steps=self.pipelineStep)
            self.pipeLine.validate()
            
            print("Publishing pipeline .....")
            self.publishedPipeline = self.pipeLine.publish(name=self.programArguments.pipeline_name, description="Dummy Pipeline")

            '''
                Now we schedule it. This step on it's own will create the AMLS experiment tied to this 
                service. 

                Unlike with the RTS example, no model is creted in this step. 

                Next we generate the schedule recurrence, when this pipeline should run, and finally create
                the schedule by identifying the published pipeline that is being requested. 
            '''
            print("Scheduling pipeline .....")
            experiment_name = "exp_" + self.programArguments.pipeline_name
            recurrence = ScheduleRecurrence(
                            frequency=self.programArguments.schedule_frequency, 
                            interval=self.programArguments.schedule_interval
                            )

            self.Schedule = Schedule.create(
                    workspace=self.workspace,
                    name = "{}_sched".format(self.programArguments.pipeline_name),
                    pipeline_id = self.publishedPipeline.id,
                    experiment_name = experiment_name,
                    recurrence = recurrence,
                    description = "Pipeline schedule for {}".format(self.programArguments.pipeline_name),
                    )

        '''
            Print out what we know of the pipeline. In particular it's status and the endpoint. 
        '''
        print("Pipeline : ", self.publishedPipeline.name )        
        print("Pipeline Endpoint: ", self.publishedPipeline.endpoint)
        print("Pipeline Status: ", self.publishedPipeline.status)
