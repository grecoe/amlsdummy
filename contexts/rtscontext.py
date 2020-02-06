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
    scoring_script = "scoring.py"

    '''
        Contains the context needed to perform the tasks. 
    '''
    def __init__(self, programArgs, userAuthorization):
        super().__init__(programArgs, userAuthorization)
        self.containerImage = None
        self.computeTarget = None
        self.webservice = None
        self.webserviceapi = {}

    def generateModel(self):
        '''
            Get an existing model by name or create new
        '''
        self.model = registerModel(
            self.workspace,
            self.experiment,
            self.programArguments.model_name,
            RealTimeScoringContext.model_file
            )

        if not self.model:
            raise Exception("Model Creation Failed")        

    def generateImage(self):
        '''
            Generates an image, get name and version using:
            print(image.name, image.version)
            Logs here:
            image.image_build_log_uri
        '''
        self.containerImage = createImage(
            self.workspace,
            RealTimeScoringContext.scoring_script,
            self.model,
            self.programArguments.image_name)

        if not self.containerImage:
            raise Exception("Container Image Creation Failed")

        print("Container Creation Log: ", self.containerImage.image_build_log_uri)

    def loadImage(self):
        '''
            In testing, I did NOT want to keep generating a model and generating an image, 
            if it loads then we've already done that step.
        '''
        if not self.containerImage:
            containers = ContainerImage.list(workspace= self.workspace, image_name = self.programArguments.image_name)
            if len(containers) > 0:
                print("Found existing image, loading...")
                self.containerImage = containers[-1]

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

    def testImage(self):
        '''
            Test the image locally only if version is Linux
        '''   
        if self.platform == 'linux':
            if not self.containerImage:
                containers = ContainerImage.list(workspace=self.workspace, image_name = self.programArguments.image_name)
                if len(containers) > 0:
                    self.containerImage = containers[-1]
        
            if self.containerImage:
                result = self.containerImage.run(json.dumps({"name": "Dave"}))
                print("RESULT: ", result)
            else:
                print("No container image found")
        else:
            print("Locat image testing only supported on Linux.")

    def generateComputeTarget(self, cluster_name = None, resource_group = None):
        '''
            Caller has to figure out if they are going to attach an existing cluster
            or create a new one. Decided based on parameters
        '''

        if self.computeTarget:
            return self.computeTarget

        if cluster_name is None and resource_group is None:
            print("Option is to create new compute target....")
            self.computeTarget = createComputeCluster(
                self.workspace, 
                self.programArguments.region, 
                self.programArguments.aks_compute_name, 
                self.programArguments.aks_vm_size, 
                self.programArguments.aks_node_count,
                self.programArguments.aks_non_prod
                )
        else:
            print("Option is to attach existing compute target....")
            self.computeTarget = attachExistingCluster(
                self.workspace, 
                cluster_name, 
                resource_group, 
                self.programArguments.aks_compute_name,
                self.programArguments.aks_non_prod
                )

        if not self.computeTarget:
            raise Exception("Cannot create compute target.")

    def generateWebService(self):
        '''
            Generate the web service
        '''
        if not self.webservice:
            self.webservice = createWebservice(
                self.workspace, 
                self.containerImage,
                self.programArguments.aks_service_name, 
                self.programArguments.aks_num_replicas, 
                self.programArguments.aks_cpu_cores, 
                self.computeTarget
                )

        if not self.webservice:
            raise Exception("Could not create the web service.")

        self.webserviceapi["url"] = self.webservice.scoring_uri
        self.webserviceapi["key"] = self.webservice.get_keys()[0]

    def testWebService(self):
        if self.webservice:
            prediction = self.webservice.run(json.dumps({"name": "Dave"}))
            print(prediction)
