import sys 
import json
import platform
from scripts.azure_utils import *
from scripts.general_utils import loadArguments

from azureml.core.image import ContainerImage

class Context:
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
        self.programArguments = programArgs
        self.authentication = userAuthorization
        self.platform = platform.system().lower()
        self.workspace = None
        self.experiment = None
        self.model = None
        self.containerImage = None
        self.computeTarget = None
        self.webservice = None
        self.webserviceapi = {}
        

        if not self.authentication:
            raise Exception("Authentication object missing")

        '''
            Change the context to the provided subscription id
            This expects that an az login has already occured with a user
            that has the correct credentials.
        '''
        setContext(self.programArguments.subid)

    def generateWorkspace(self):
        '''
            Gets an existing workspace (by name) or creates a new one
        '''
        
        self.workspace = getWorkspace(
            self.authentication, 
            self.programArguments.subid, 
            self.programArguments.resourceGroup,
            self.programArguments.workspace,
            self.programArguments.region
            )

        if not self.workspace:
            raise Exception("Workspace Creation Failed")

    def generateExperiment(self):
        '''
            Get an existing experiment by name, or create new
        '''
        self.experiment = getExperiment(self.workspace, self.programArguments.experiment)

        if not self.experiment:
            raise Exception("Experiment Creation Failed")

    def generateModel(self):
        '''
            Get an existing model by name or create new
        '''
        self.model = registerModel(
            self.workspace,
            self.experiment,
            self.programArguments.model_name,
            Context.model_file
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
            Context.scoring_script,
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
            containers = ContainerImage.list(workspace=program_context.workspace, image_name = self.programArguments.image_name)
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
                containers = ContainerImage.list(workspace=program_context.workspace, image_name = self.programArguments.image_name)
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



'''
    Program Code:

    Program will use settings from general_utils.py where user can optionally pass in parameters or 
    use the defaults set up. Those parameters and the user authentication are held in the Context class
    defined above. 

    Since this can be run in steps to slowly build up the service (as I did when creating this), each step
    validates if the object or service needs to be created. If it already exists (generally based on name)
    a new object/service is not created and the existing object/service is preserved in the Context class.

    Also note, each step needs to be performed in order (listed here) so that the appropriate objects/services
    are collected before trying to use them. 

    For details about the steps performed read:

    https://github.com/grecoe/amlsdummy#script-runpy
  
'''


'''
    Get the program arguments and user authentication into the context
'''
programargs = loadArguments(sys.argv[1:]) 
userAuth = get_auth()
program_context = Context(programargs, userAuth)

'''
    Get a workspace
'''
program_context.generateWorkspace()

'''
    Get or create an experiment
'''
program_context.generateExperiment()

'''
    Get existing or create and register model
'''
program_context.generateModel()

'''
    Create or update the container image
'''
if program_context.loadImage() == False:
    program_context.generateImage()
    program_context.testImage()

'''
    Create/attach existing compute target

    To attach, you have to provide the cluster name and resource group name
    in the program arguments. By default they are set to None so that a new cluster
    is generated.
'''
program_context.generateComputeTarget(
     cluster_name = program_context.programArguments.aks_existing_cluster,
     resource_group = program_context.programArguments.aks_existing_rg
     )

'''
    Create service
'''
program_context.generateWebService()
print(program_context.webserviceapi)
program_context.testWebService()