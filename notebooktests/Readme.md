# IPYNB Notebooks

While there is  a package out there to do parameter replacements inside of IPYNB files (cookiecutter) this folder contains a home rolled version that is slightly different.

1. Identify multiple ipynb files at once to process
2. Identify one or more cell tags to look for
3. Spell out name/value replacements for tagged cells in configuraiton. 
4. Execute all ipynb files

See notebooktest.py for execution notes and testconfig.json for an example configuration. Currently the two notebooks in /notebooks WILL have modifications made before running them so you can try it out.

## NOTE
You have to execute this in a conda environment, use ipythonenv.yml to create a new environment for this work. 