import os
import json
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError


def load_notebook(nbfile):
    """
    Load an ipynb file using nbformat
    """
    notebook = None
    notebook_content = None
    with open(nbfile,"r") as f:
        notebook_content = f.readlines()
        notebook_content = "\n".join(notebook_content)

    if notebook_content:        
        notebook = nbformat.reads(notebook_content, as_version=4)

    return notebook


def load_configuration(config):
    """
    Load configuration with tags and replacement formats
    """
    notebooks = []
    tag_replacements = {}    
    config_content = None

    with open(config,"r") as f:
        config_content = f.readlines()
        config_content = "\n".join(config_content)

    if config_content:
        config_content = json.loads(config_content)

        notebooks.extend(config_content['notebooks'])

        for cf in config_content['replacements']:
            tag_replacements[cf['tag']] = cf['values']
    
    return notebooks, tag_replacements


def split_source(source):
    """
    Break source up into individual lines (as it appears)
    """
    if '\r\n' in source:
        return source.split('\r\n')
    elif '\n' in source:
        return source.split('\n')

    return source


def split_source_line(line):
    """
    Break down a line ONLY if it has a '=' in it. Take everything left 
    and right from assignment.
    """    
    return_value = []
    if '=' in line:
        idx = line.index('=')
        return_value.append(line[0:idx].strip())
        return_value.append(line[idx+1:].strip())

    return return_value        


def update_notebook(notebook, build_tags):
    """
    If a notebook has tags and that tag is listed in the configuraiton, 
    split all lines with '=' in it into right/left. 

    If right is in the replacement names replace left with the value from
    the configuraiton. 

    Then write out the source cell to the notebook again. 
    """

    if notebook["cells"] and build_tags:

        """
        Filter for cells that :
            1. Are code cells
            2. Have metadata
            3. Have 'tags' field in metadata 
        """
        code_cells = [
            x for x in notebook['cells'] 
            if x['cell_type'] == 'code' 
            and len(x['metadata'])
            and 'tags' in x['metadata']
        ]

        # All of these we know have tags associated
        for tag in build_tags.keys():
            # Go through our tags to see if it applies
            current_cells = [ x for x in code_cells if tag in x['metadata']['tags']]

            for current in current_cells:
                # It's one we are after, now go through the source and parse out
                # formats of XXX = YYYY and if present, we have to update it.
                raw_source = split_source(current['source'])

                # If there is only one, it comes back as a string not a list
                if isinstance(raw_source, str):
                    raw_source = [raw_source]
                        
                modified = False
                for line_idx in range(len(raw_source)):
                    # Single line
                    line = raw_source[line_idx]
                    # Split left=right
                    res = split_source_line(line)
                    # Adjust if neccesary
                    if len(res) == 2:
                        replacement = None if res[0] not in build_tags[tag] else build_tags[tag][res[0]]
                        if replacement:
                            updated = "{}={}".format(
                                res[0],
                                '"{}"'.format(replacement) if isinstance(replacement,str) else replacement
                            )
                            raw_source[line_idx] = updated
                            modified = True

                if modified:
                    # If we've modified anything, update the source
                    current['source'] = "\n".join(raw_source)


def execute(notebook, notebook_path, kernel="python3"):
    """
    Execute the notebook and create the ouptut file. 
    """
    try:
        nb_path = os.path.split(notebook_path)[0] + '/'
        ep = ExecutePreprocessor(timeout=600, kernel_name=kernel)
        retval = ep.preprocess(nb, {'metadata': {'path': nb_path}})

        for item in retval:
            if isinstance(item, nbformat.notebooknode.NotebookNode):
                output_path = notebook_path.replace('.ipynb', '_output.ipynb')
                with open(output_path, mode="w", encoding="utf-8") as f:
                    nbformat.write(item, f)                
        
    except CellExecutionError as ex:
        print("Execution Exception in notebook({}):".format(notebook_path))
        print(str(ex))



# Load configuration with tag names and replacement values
notebooks, tag_replacements = load_configuration("./testconfig.json")

# Execute each notebook with replacements as needed
for notebook_path in notebooks:
    print("Processing", notebook_path)
    # Load the notebook
    nb = load_notebook(notebook_path)
    print("Config loaded")
    # Change data, if neccesary
    update_notebook(nb,tag_replacements)
    print("Notebook updated")
    # Execute the notebook
    execute(nb,notebook_path)
    print("Notebook executed")
