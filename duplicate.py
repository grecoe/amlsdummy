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


def _loadConfiguration(configuration_file):
    '''
        If the program is started with two arguments:
            -config [filename]
        
        The settings for the program will strictly be loaded from the configuration
        file, bypassing any other provided arguments AND the default settings in 
        loadArguments()

        When reading in a json null, Python converts it to the string None. Make 
        sure we catch these. 
    '''
    return_settings = []
    config_json = None
    if configuration_file:
        if os.path.exists(configuration_file) :
            with open(configuration_file,"r") as input_config:
                config_content = input_config.read()
                config_json = json.loads(config_content)

    for key in config_json:
        return_settings.append('-' + key)
        value = config_json[key]
        if value == None or value == 'None':
            return_settings.append(None)
        else:
            return_settings.append(str(value))

    return return_settings

def loadArguments(sys_args):
    '''
        Loads the arguments for the program. 
        User has the choice to:
        1. Provide no arguments -> Use defaults in this function
        2. -config [filename] as the only 2 arguments -> Load the settings from the configuration file
        3. Multiple arguments -> Use the provided arguments
    '''
    load_configuration = False
    if len(sys_args) == 0:
        print("Using default settings in loadArguments()")
    elif '-config' in sys_args and len(sys_args) == 2:
        print("Load configuration file for settings." , sys_args[1])
        sys_args = _loadConfiguration(sys_args[1])
    else:
        print("User provided settings will be used (along with any defaults not specified)")

    '''
        All of the parameters needed to execute a succesful deployment. These can simply be set here 
        so that you can run run.py without any additional parameters OR you can pass in one or many
        of the 13 settings.
    '''
    parser = argparse.ArgumentParser(description='Simple model deployment.') 

    '''
        Subscription information : Subscription ID, Resource Group, Region
    '''
    parser.add_argument("-subid", required=False, default='0ca618d2-22a8-413a-96d0-0f1b531129c3', type=str, help="Subscription ID") 
    parser.add_argument("-resourceGroup", required=False, default="dangtestbed", type=str, help="Resource Group") 
    parser.add_argument("-region", required=False, default="eastus", type=str, help="Azure Region") 
    '''
        AMLS Workspace infomration: workspace name
    '''
    parser.add_argument("-workspace", required=False, default="dangws", type=str, help="Workspace name") 
    '''
        AMLS Exeriment informaiton:
            - Experiment name
            - Model name (that will be registered)
            - Docker container image name
    '''
    parser.add_argument("-experiment", required=False, default="simple_experiment", type=str, help="Experiment name") 
    parser.add_argument("-model_name", required=False, default="dummy", type=str, help="Registered model name") 
    parser.add_argument("-image_name", required=False, default="simplemodel", type=str, help="Docker container name")
    '''
        AKS Information

            Information for adding or attaching an AKS cluster as an Inference Compute to 
            the AMLS workpsace. 

            IMPORTANT : If aks_existing_cluster and aks_existing_rg are NOT None, then 
                        the program will try and attach, not create a new cluster. 

            COMMON FIELDS - ADD OR ATTACH
                - aks_compute_name - AKS Compute name in AMLS Workspace
                - aks_service_name - AKS Service name (the name of the generated webservice)
                - aks_non_prod - If this flag is set AND the cluster is to be created or attached
                        then the configuration will include the following flag:
                            cluster_purpose = AksCompute.ClusterPurpose.DEV_TEST
                        Essentially, this means that the cluster you are attaching or requesting 
                        would not be suitable for production. For more information see here:

                        https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-azure-kubernetes-service#create-a-new-aks-cluster

            ATTACH CLUSTER INFORMATION
                - aks_existing_cluster - Name of an existing AKS cluster to attach
                - aks_existing_rg - Resource group in which the existing cluster lives in.

            CREATE CLUSTER INFORMATION
                - aks_vm_size - The type of VM to create the cluster with
                - aks_node_count - The number of VM's to add to the cluster
                - aks_num_replicas - The number of instances of the container running in the cluster.
                - aks_cpu_cores - Number of cores to allocate to each replica
    ''' 
    # Common
    parser.add_argument("-aks_compute_name", required=False, default="dummyaks", type=str, help="AMLS Compute Name") 
    parser.add_argument("-aks_service_name", required=False, default="dummycluster", type=str, help="AKS Service Name") 
    parser.add_argument("-aks_non_prod", required=False, default=False, type=bool, help="Indicates if the cluster is production level or not.") 
    
    # Attach
    parser.add_argument("-aks_existing_cluster", required=False, default=None, type=str, help="AKS VM node SKU") 
    parser.add_argument("-aks_existing_rg", required=False, default=None, type=str, help="AKS VM count in cluster") 

    # Create
    parser.add_argument("-aks_vm_size", required=False, default="Standard_D4_v2", type=str, help="AKS VM node SKU") 
    parser.add_argument("-aks_node_count", required=False, default=4, type=int, help="AKS VM count in cluster") 

    # Web Service Parameters
    parser.add_argument("-aks_num_replicas", required=False, default=2, type=int, help="AKS replica count of generated container.") 
    parser.add_argument("-aks_cpu_cores", required=False, default=1, type=int, help="Number of cores to allocate to each replica") 

    parsed_arguments = parser.parse_args(sys_args)

    '''
        For some reason, when loading from JSON and leaving None in the 
        input array for parser.parse_args, those values are getting turned 
        into the String None, correct that here.
    '''
    for attr, value in parsed_arguments.__dict__.items():
        if value == 'None':
            setattr(parsed_arguments, attr, None)


    return parsed_arguments






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
            RealTimeScoringContext.model_file
            )

        if not self.model:
            raise Exception("Model Creation Failed")

