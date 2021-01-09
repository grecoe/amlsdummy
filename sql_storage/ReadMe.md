# Azure Storage Utilities

This utility makes using Azure Blob Storage easier by wrapping it in a class and masking some of the many options that are not neccesarily needed for simple blob storage operations. 

It does, however, require that an Azure Storage package be installed either in your environment or a Conda environment. For simplicity, this project includes a file to set up a simple Conda environment to test out the functionality - __StorageTestEnv__. 

```
conda env create -f environment.yml
```

The __example.py__ file shows examples on how to create an instance of the __StorageUtils__ class and how to use it to iterate containers, blobs, upload and download files to and from the Azure Storage account. 