from utils import Logger, FunctionTrace, Configuration, NotebookUtil

# Load configuration 
config = Configuration()
config.load_configuration("./testconfig.json")

if not len(config.notebooks):
    Logger.add_log("No notebooks identified in configuration")
    quit()

if not len(config.tags):
    Logger.add_log("No tags identified in configuration")
    quit()

# Execute each notebook with replacements as needed
for notebook_path in config.notebooks:
    try:
        print("Processing {}".format(notebook_path))
        nb_util = NotebookUtil(notebook_path)
        nb_util.update_notebook(config.tags)
        success = nb_util.execute()
        if not success:
            print("Notebook {} failed to execute".format(notebook_path))
            break
        print("Notebook execution complete")
    except Exception as ex:
        message = "{} failed with {}".format(notebook_path, str(ex))
        Logger.add_log(message)
        print(message)
        break

print("Execution complete")   