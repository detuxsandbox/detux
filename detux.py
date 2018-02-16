# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

# Import Detux packages
from core.sandbox import Sandbox
from core.report import Report

# import other python packages
import json
import sys
import os
import argparse
import requests


from ConfigParser import ConfigParser


config_file = "detux.cfg"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--sample', help = "Sample path", required=True)
    parser.add_argument('--cpu',  help = "CPU type", choices = ['x86', 'x86-64', 'arm', 'mips', 'mipsel'], default = 'auto')
    parser.add_argument('--int',  help = "Architecture type", choices = ['python', 'perl', 'sh', 'bash'], default = None)
    parser.add_argument('--report', help = "JSON report output path",  required=True)

    args = parser.parse_args()

    sample_path = args.sample
    cpu = args.cpu
    interpreter = args.int
    report_path = args.report 

    print "> Processing", sample_path
    
    # Process the sample with sandbox
    sandbox = Sandbox(config_file)
    

    if cpu == 'auto':
        filetype, platform = sandbox.identify_platform(sample_path)
        print "> CPU:", platform
        cpu = platform
    print "> Interpreter:", interpreter
    result = sandbox.execute(sample_path, cpu, '1', interpreter)

    # Process the sanbox result to prepare a DICT report
    reporter =  Report(sample_path, result)

    print "> Generating report"
    # Retrive the report
    report = reporter.get_report()

    # Dump the Report in JSON format

    json_report = json.dumps(report, indent=4, sort_keys=True)
    
    with open(report_path, 'w') as f:
        f.write(json_report)
    
    print "> Report written to", report_path  

    # Store Result in ES
    config = ConfigParser()
    config.read(config_path)
    es_enabled = config.get("es", "es_enabled")
    es_url = config.get("es", "es_server")
    

    if es_enabled == True:
        result = requests.put( es_server + "/reports", data=json_report)

  
    


