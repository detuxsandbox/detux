#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

# Import Detux packages
from core.sandbox import Sandbox
from core.report import Report
from core.objects import SandboxRun, Hypervisor

# import other python packages
import json
import sys
import os
import argparse

config_file = "detux.cfg"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--sample', help= "Sample path", required=True, dest='sample_path')
    parser.add_argument('--cpu',  help= "CPU type", choices= ['x64'], default= 'auto', dest='cpu')
    parser.add_argument('--os',  help= "Operating System type", choices= ['windows', 'linux'], default= 'auto', dest='os')    
    parser.add_argument('--int',  help= "Architecture type", choices= ['python', 'perl', 'sh', 'bash'], default= None, dest='interpreter')
    parser.add_argument('--timeout',  help= "Set sample runtime", type=int, default= 300, required=False, dest='timeout')
    parser.add_argument('--report', help= "JSON report output path",  required=True, dest='report_path')
    parser.add_argument('--arguments', help= "Sample Arguments",  required=False, dest='sample_args')

    args = parser.parse_args()
    cpu = ""

    print("> Processing", args.sample_path)
    print("> Args:", args.sample_args)

    # Setup our sample run 
    samplerun = SandboxRun(args.sample_path, args.sample_args, args.cpu, args.os, args.timeout)

    # Setup our handle the the hypervisor 
    hypervisor = Hypervisor()

    # Setup our Sandbox handle
    sandbox = Sandbox(config_file, hypervisor)

    # Setup report handle
    report = Report(samplerun)

    print("> CPU:", samplerun.platform)
    print("> FileType:", samplerun.filetype)
#
#    print("> Interpreter:", args.interpreter)
    #IN:   sandbox.execute( samplerun )
    #OUT:  dict(REPORT)


#    print(hypervisor.list_vms())


    result = sandbox.run(samplerun, report)

#    print("> Generating report")
#    # Retrive the report and  Process the sanbox result to prepare a DICT report
#    reporter =  Report(args.sample_path, result)
#    report = reporter.get_report()
#
#    # Dump the Report in JSON format
#    json_report = json.dumps(report, indent=4, sort_keys=True)
#
#    with open(args.report_path, 'w') as f:
#        f.write(json_report)
#    
#    print("> Report written to", args.report_path    )
    


