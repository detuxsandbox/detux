#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

# Import Detux packages
from core.sandbox import Sandbox
from core.report import Report

# import other python packages
import json
import sys
import os
import argparse

config_file = "detux.cfg"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--sample', help = "Sample path", required=True, dest='sample_path')
    parser.add_argument('--cpu',  help = "CPU type", choices = ['x86', 'x86-64', 'arm', 'mips', 'mipsel'], default = 'auto', dest='cpu')
    parser.add_argument('--int',  help = "Architecture type", choices = ['python', 'perl', 'sh', 'bash'], default = None, dest='interpreter')
    parser.add_argument('--timeout',  help = "Set sample runtime", type=int, default = None, required=False, dest='timeout')
    parser.add_argument('--report', help = "JSON report output path",  required=True, dest='report_path')
    parser.add_argument('--arguments', help = "Sample Arguments",  required=False, dest='sample_args')

    args = parser.parse_args()
    cpu = ""

    print("> Processing", args.sample_path)
    
    # Process the sample with sandbox
    sandbox = Sandbox(config_file)

    print("> Args:", args.sample_args)
    
    if args.cpu == 'auto':
        filetype, platform = sandbox.identify_platform(self.sample_path)
        print("> CPU:", args.platform)
        cpu = platform
    else:
        cpu = args.cpu

    print("> CPU:", cpu )
    print("> Interpreter:", args.interpreter)
    #IN:   sandbox.execute( FILEPATH, CPU PLATFORM, SANDBOX_ID, INTERPRETER, TIMEOUT)
    #OUT:  dict(REPORT)
 


    result = sandbox.execute(args.sample_path, args.sample_args, cpu, '1', args.interpreter, args.timeout)

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
    


