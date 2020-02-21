import shutil
from scripts.azure_utils import *
from contexts.basecontext import BaseContext

class RealTimeScoringContext(BaseContext):
    '''
        Model file and scoring script. These are constants and 
        probably no need to update them. 

        The remainder of the needed configuration comes from 
        the program arguments parsed in general_utils.py
    '''
    model_file = "model.pkl"
    scoring_script_name = "./scoring.py"
    scoring_script = "./paths/realtime/scoring/scoring.py"

    '''
        Contains the context needed to perform the tasks. 
    '''
    def __init__(self, programArgs, userAuthorization, job_log = None):
        super().__init__(programArgs, userAuthorization, job_log)
        self.containerImage = None
        self.computeTarget = None
        self.webservice = None
        self.webserviceapi = {}

    def generateModel(self):
        '''
            Get an existing model by name or create new
        '''
        self.model = getOrRegisterModel(
            self.workspace,
            self.experiment,
            self.programArguments.model_name,
            RealTimeScoringContext.model_file,
            self.job_log
            )

        if not self.model:
            raise Exception("Model Creation Failed")        

    def generateImage(self):
        '''
            Generates a docker image, get name and version using:
            print(image.name, image.version)
            Logs here:
            image.image_build_log_uri

            Move the scoring script to the execution directory (which is a requirement for creating an image)
            When done, remove the copy.
        '''
        shutil.copyfile(RealTimeScoringContext.scoring_script, RealTimeScoringContext.scoring_script_name)
        self.containerImage = createImage(
            self.workspace,
            RealTimeScoringContext.scoring_script_name,
            self.model,
            self.programArguments.image_name,
            self.job_log)

        if not self.containerImage:
            raise Exception("Container Image Creation Failed")

        print("Container Creation Log: ", self.containerImage.image_build_log_uri)

    def loadImage(self):
        '''
            In testing, I did NOT want to keep generating a model and generating an image, 
            if it loads then we've already done that step.
        '''
        if not self.containerImage:
            self.containerImage = getExistingContainerImage(self.workspace, self.programArguments.image_name, self.job_log )
            
        if self.containerImage != None:
            '''
                With CMK testing, we really need to check this....it's possible an image 
                was attempted but the actual build failed as it happens on ACR. This means
                that AMLS will record that it has an image, but the image state comes back
                failed. 
            '''
            if self.containerImage.creation_state == "Failed":
                raise Exception("Image exists but state is failed, terminating process...")

        return self.containerImage != None

    def generateComputeTarget(self, cluster_name = None, resource_group = None):
        '''
            Caller has to figure out if they are going to attach an existing cluster
            or create a new one. Decided based on parameters
        '''

        if self.computeTarget:
            return self.computeTarget

        if cluster_name is None and resource_group is None:
            print("Option is to create new compute target....")
            self.computeTarget = getOrCreateComputeCluster(
                self.workspace, 
                self.programArguments.region, 
                self.programArguments.aks_compute_name, 
                self.programArguments.aks_vm_size, 
                self.programArguments.aks_node_count,
                self.programArguments.aks_non_prod,
                self.job_log
                )
        else:
            print("Option is to attach existing compute target....")
            self.computeTarget = attachExistingCluster(
                self.workspace, 
                cluster_name, 
                resource_group, 
                self.programArguments.aks_compute_name,
                self.programArguments.aks_non_prod,
                self.job_log
                )

        if not self.computeTarget:
            raise Exception("Cannot create compute target.")
    
    def deleteWebservice(self):
        if not self.webservice:
            raise Exception("No web service loaded")
        
        print("Deleting web service...")
        self.job_log.addInfo("Deleting web service")
        self.webservice.delete()
        self.webservice = None
        self.job_log.addInfo("Web service deleted")

    def loadWebservice(self):
        '''
            Retrieve an existing web service, used for deletion purposes. 
        '''
        if not self.workspace:
            raise Exception("You must load the workspace first")

        if not self.containerImage:
            raise Exception("You must load the conatiner image first")

        if not self.webservice:
            self.webservice = getExistingWebService(
                self.workspace, 
                self.containerImage,
                self.programArguments.aks_service_name, 
                self.job_log
                )

        return self.webservice != None

    def generateWebService(self):
        '''
            Generate the web service
        '''
        if not self.webservice:
            self.webservice = getOrCreateWebservice(
                self.workspace, 
                self.containerImage,
                self.programArguments.aks_service_name, 
                self.programArguments.aks_num_replicas, 
                self.programArguments.aks_cpu_cores, 
                self.computeTarget,
                self.job_log
                )

        if not self.webservice:
            raise Exception("Could not create the web service.")

        self.webserviceapi["url"] = self.webservice.scoring_uri
        self.webserviceapi["key"] = self.webservice.get_keys()[0]

    def testWebService(self):
        if self.webservice:
            prediction = self.webservice.run(json.dumps({"name": "Dave"}))
            print(prediction)
