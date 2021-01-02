import os
import nbformat # pylint: disable=import-error
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError # pylint: disable=import-error
from utils import FunctionTrace, Logger

class NotebookUtil:
    def __init__(self, notebook_path):
        self.notebook_path = notebook_path
        self.notebook = None

        # Set up trace
        self._load_notebook = FunctionTrace(self._load_notebook)
        self._split_source = FunctionTrace(self._split_source)
        #self._split_source_line = FunctionTrace(self._split_source_line)
        self.update_notebook = FunctionTrace(self.update_notebook)
        self.execute = FunctionTrace(self.execute)

        # Load up notebook
        self.notebook = self._load_notebook(self.notebook_path)
 
    def update_notebook(self, notebook_tags): # pylint: disable=method-hidden
        """
        If a notebook has tags and that tag is listed in the configuraiton, 
        split all lines with '=' in it into right/left. 

        If right is in the replacement names replace left with the value from
        the configuraiton. 

        Then write out the source cell to the notebook again. 
        """
        modification_count = 0

        if self.notebook["cells"] and notebook_tags:

            """
            Filter for cells that :
                1. Are code cells
                2. Have metadata
                3. Have 'tags' field in metadata 
            """
            code_cells = [
                x for x in self.notebook['cells'] 
                if x['cell_type'] == 'code' 
                and len(x['metadata'])
                and 'tags' in x['metadata']
            ]

            # All of these we know have tags associated
            for tag in notebook_tags.keys():
                # Go through our tags to see if it applies
                current_cells = [ x for x in code_cells if tag in x['metadata']['tags']]

                for current in current_cells:
                    # It's one we are after, now go through the source and parse out
                    # formats of XXX = YYYY and if present, we have to update it.
                    raw_source = self._split_source(current['source'])

                    # If there is only one, it comes back as a string not a list
                    if isinstance(raw_source, str):
                        raw_source = [raw_source]
                        
                    modified = False
                    for line_idx in range(len(raw_source)):
                        # Single line
                        line = raw_source[line_idx]
                        # Split left=right
                        res = self._split_source_line(line)
                        # Adjust if neccesary
                        if len(res) == 2:
                            replacement = None if res[0] not in notebook_tags[tag] else notebook_tags[tag][res[0]]
                            if replacement:
                                modification_count += 1
                                updated = "{}={}".format(
                                    res[0],
                                    '"{}"'.format(replacement) if isinstance(replacement,str) else replacement
                                )
                                raw_source[line_idx] = updated
                                modified = True

                    if modified:
                        # If we've modified anything, update the source
                        current['source'] = "\n".join(raw_source)

        return modification_count

    def execute(self, kernel="python3"): # pylint: disable=method-hidden
        """
        Execute the notebook and create the ouptut file. 
        """
        executed = True

        try:
            nb_path = os.path.split(self.notebook_path)[0] + '/'
            ep = ExecutePreprocessor(timeout=600, kernel_name=kernel)
            retval = ep.preprocess(self.notebook, {'metadata': {'path': nb_path}})

            for item in retval:
                if isinstance(item, nbformat.notebooknode.NotebookNode):
                    output_path = self.notebook_path.replace('.ipynb', '_output.ipynb')
                    with open(output_path, mode="w", encoding="utf-8") as f:
                        nbformat.write(item, f)                
        
        except CellExecutionError as ex:
            executed = False
            Logger.add_log("CellExecutionError in notebook({}):".format(self.notebook_path))
            Logger.add_log(str(ex))

        return executed

    def _load_notebook(self, nbfile): # pylint: disable=method-hidden
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


    def _split_source(self, source): # pylint: disable=method-hidden
        """
        Break source up into individual lines (as it appears)
        """
        if '\r\n' in source:
            return source.split('\r\n')
        elif '\n' in source:
            return source.split('\n')

        return source


    def _split_source_line(self, line): # pylint: disable=method-hidden
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
