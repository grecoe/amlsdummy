import sys 
import json
import platform
from scripts.azure_utils import get_auth, setContext, getWorkspace, getExperiment, registerModel, createImage, createComputeCluster, attachExistingCluster, createWebservice
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
            self.computeTarget = createComputeCluster(
                self.workspace, 
                self.programArguments.region, 
                self.programArguments.aks_name, 
                self.programArguments.aks_vm_size, 
                self.programArguments.aks_node_count
                )
        else:
            self.computeTarget = attachExistingCluster(
                self.workspace, 
                cluster_name, 
                resource_group, 
                self.programArguments.aks_name
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

    Steps that occur:
    1. Create the context object
    2. Generate an Azure Machine Learning Service Workspace
        - If workspace already exists by name in the sub with the provided resource group, 
          that workspace it will be added to the Context object. 
        - If it doesn't exist it is created and added to the Context object.
    3. Generate the AMLS Experiment
        - If the experiment exists in the workspace by name, it will be added to the Context object.
        - If the experiment doesn't exist it is created and added to the Context object..
    4. Create a model
        This is really a no-op model. A pkl file is generated from nothing useful, but the 
        model file is required to create a container.
        - If the model already exists by name it will be added to the Context object
        - If it doesn't exist, a simple pkl file is generated and registered as a new model. The 
          result is added to the Context object.
    5. Create a conatiner image. 
        - Attempts to load a container image associated with the current workspace. 
            - If found, it is added to the Context object
            - If not found, creates a new container image and adds it to the Context object.
                - It is ok to just create new images, it just updates the version in the ACR
                - Once the image is created, attempts to test the container image locally. However
                  this is a Linux based image so if the current system is not Linux test will 
                  not run. 
    6. Creates or attaches a compute target (in this case AKS)
        - If you have a cluster alreayd, use the function Context.generateComputeTarget by supplying 
          the cluster name and resource group. The existing cluster is then added to the Context object.
        - If you need a new cluster, leave those fields blank and:
            - If a compute with the same name is already associated with the workspace, that compute 
              is added to the Context object.
            - If a compute doesn't exist, it is created and added to the Context object.
    7. Create the web service to serve up the REST api endpoint.
        - If a service already exists in the workspace for the expected container image name, that 
          service is added to the Context object.
        - If the service doessn't exist, a new one is created and added to the Context object.
    8. The web service is tested and the result is printed to the console along with the connection
       info for the service, i.e. URI and KEY. When this succeeds, you can take that connection info
       and use it elsewhere. 
        - If you don't record the API information, you can simply re-run this script and it will be collected
          for you without creating any new objects/resources (assuming you have not changed the configuration)

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
    Create service
'''
program_context.generateComputeTarget()

'''
    Create service
'''
program_context.generateWebService()
print(program_context.webserviceapi)
program_context.testWebService()