# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

import os
import time

class Report:
    def __init__(self, samplerun):
        #self.samplerun = samplerun
        #self.hashes = samplerun.hashes

        #self.report_dir = "./reports/{}-{}".format(int(time.time()), self.hashes['sha256'])

        self.report = {}
        self.new_processes = []
        self.ended_processes = []
        self.execution_log = ""

        #self.setup()

       # print("> Report Dir: {}".format(self.report_dir))

    def setup(self):
        if not os.path.isdir(self.report_dir):
            os.mkdir(self.report_dir)


    def process_ps_results(self, start, end):
        print("diff start-end") #TODO
        s_ps1 = ps1.split('\n')
        s_ps2 = ps2.split('\n')
        for p_post in [i for i in s_ps2 if i not in s_ps1 ]:
            rec = p_post.lstrip().split(' ')
            self.new_processes.append(rec)

        for p_pre in [i for i in s_ps1 if i not in s_ps2 ]:
            rec = p_post.lstrip().split(' ')
            self.ended_processes.append(rec)


        print(self.new_processes)
        print(self.ended_processes)
        



if __name__ == "__main__":
    r = Report(None)


    ps1 = open('ps1').read()
    ps2 = open('ps2').read()


    r.process_ps_results(ps1, ps2)