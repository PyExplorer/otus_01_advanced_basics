Homework for 01_advanced_basics

Taras Shevchenko

Log Analyzer
=======

INSTALLATION
----------

| Directory tree    |Contents |
| --- | --- |
|  src/             |     source code               |
|  tests/           |     tests                     |  
|  tests/log        |     samples for testing needs |
|  requirements.txt |     requirements              |
|  LICENSE          |     license                   |  
|  README           |     this file                 |

REQUIREMENTS
--------
The minimum requirement is python 2.7

No external packages are needed

QUICK START
-------
At first we should go to src/

$cd src

Then she script can be run with the one of the next lines:

$python log_analyzer.py

$python log_analyzer.py -c 'extconfig.json'

$python log_analyzer.py --config 'extconfig.json'

DESCRIPTION
----
1. If we do not specify an external configuration file - is taken by default as 'config.json'

2. The config for a job is the merged version of both - internal and external configs with precedence for external
    
3. config.json is:

{
  "REPORT_SIZE": 2000, # max number of lines to report sorted by time_sum
  
  "REPORT_DIR": "./reports", # directory for reports
  
  "LOG_DIR": "./log", # directory for logs for parsing
  
  "LOG_FILE": "./analyzer.log", # log file with messages about a job
  
  "TS_FILE": "./log_analyser.ts" # file with timestamps
}

TESTS
-----

Tests can be run from command line with

python -m unittest discover -s . -p test_analyzer.py -t .
