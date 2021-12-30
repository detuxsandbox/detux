# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

import os
import time

class Report:
    def __init__(self, samplerun):
        self.samplerun = samplerun
        self.hashes = samplerun.hashes

        self.report_dir = "./reports/{}-{}".format(int(time.time()), self.hashes['sha256'])

        self.report = {}
        self.uniq_procs = []
        self.execution_log = ""

        self.setup()

    def setup(self):
        if not os.path.isdir(self.report_dir):
            os.mkdir(self.report_dir)


    def process_results(self, start, end):
        print("diff start-end") #TODO
        self.uniq_procs = []

