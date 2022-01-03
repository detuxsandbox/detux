#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

# Import Detux packages
from core.sandbox import Sandbox
from core.report import Report
from core.Hypervisor import Hypervisor
from core.SandboxRun import SandboxRun

from core.common import new_logger
log = new_logger("main")

# import other python packages
import sys
import os
import argparse

config_file = "detux.cfg"

def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--sample', help= "Sample path", required=True, dest='sample_path')
    parser.add_argument('--cpu',  help= "CPU type", choices= ['x64'], default= 'auto', dest='cpu')
    parser.add_argument('--os',  help= "Operating System type", choices= ['windows', 'linux'], default= 'auto', dest='os')    
    parser.add_argument('--timeout',  help= "Set sample runtime", type=int, default= 300, required=False, dest='timeout')
    parser.add_argument('--arguments', help= "Sample Arguments",  required=False, dest='sample_args')

    return  parser.parse_args()    

if __name__ == "__main__":
    args = parse_args()

    # Setup our sample run 
    samplerun = SandboxRun(args)

    # Setup our handle the the hypervisor 
    hypervisor = Hypervisor()

    # Setup our Sandbox handle
    sandbox = Sandbox(config_file, hypervisor)

    report = Report(samplerun)
    result = sandbox.run(samplerun, report)

