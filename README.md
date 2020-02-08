# Simple Models
<sup> Daniel Grecoe - A Microsoft Employee</sup>

The code in this repository can create Azure Machine Learning services. There are two flavors of these:
1. Real Time Scoring web service
2. Batch Scoring service


# Common Configuration

## Conda Environment
Either path you choose you need to set up a conda environment to execute the scripts in as required Azure and Azure Machine Learning modules need to be present. 

1. Clone this repo to your machine
2. Create the conda environment
    - conda env create -f environment.yml
    - conda activate SimpleModel
3. Choose the path you want to follow:
    - Real Time Scoring - Navigate to  rtsreadme.md 
    - Batch Scoring - Navigate to batchreadme.md

## Logging
Regardless of path you execute, upon completion of either the rtscreate.py or batchcreate.py a log file directory is created with the following:

|Item|Type|Description|
|--|--|--|
|Logs|Directory|Holds all logs regardless of path executed.|
|Overview.csv|File|Generic CSV with three columns:<br><br>Path Type<br>Output Log File Name/Path<br>Execution Length in Seconds|
|BatchScoringLogs|Directory|Holds any log all  batchcreate.py runs. Each run creates it's own timestamped log file.|
|RealTimeScoringLogs|Directory|Holds any log all  rtscreate.py runs. Each run creates it's own timestamped log file.|