import json
from utils import FunctionTrace, Logger


class Configuration:
    """
    Describe config file structure
    """
    def __init__(self):
        self.notebooks = []
        self.tags = {}
        self.load_configuration = FunctionTrace(self.load_configuration)


    def load_configuration(self, config): # pylint: disable=method-hidden
        """
        Load configuration with tags and replacement formats
        """
        config_content = None

        with open(config,"r") as f:
            config_content = f.readlines()
            config_content = "\n".join(config_content)

        if config_content:
            config_content = json.loads(config_content)

            self.notebooks.extend(config_content['notebooks'])

            for cf in config_content['replacements']:
                self.tags[cf['tag']] = cf['values']
    
        Logger.add_log("Notebooks: {} ".format(self.notebooks))
        Logger.add_log("Tags: {} ".format(self.tags))
