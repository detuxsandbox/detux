#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import os
import re
import sys
import time
import json
import signal
import subprocess

import hashlib
from magic import Magic

from core.common import new_logger

from core.analyzer import HostAnalzer_Linux, save_files

class PCAPHandler(object):
    def __init__(self, report, target_env):
        self.log = new_logger("PCAPHandler")
        self.active = False
        self.report_pcap = "{}/report.pcap".format(report.report_dir)
        self.interface = target_env.dhcp.get('iface', None)


    def start(self):
        if self.interface == None:
            self.log.error("No interface!")
            self.start()

        self.log.info("> Starting Network Logging")
        cmd = "tcpdump -nn -i {INTERFACE} -w {REPORT_PCAP}".format(INTERFACE=self.interface, REPORT_PCAP=self.report_pcap)
        self.handle = subprocess.Popen(cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
            )

    def stop(self):
        os.killpg(os.getpgid(self.handle.pid), signal.SIGTERM)
        #self.handle.kill()



class Report:
    def __init__(self, samplerun):
        self.log = new_logger("Report")

        self.samplerun = samplerun
        self.hashes = samplerun.hashes

        self.report_dir = "./reports/{}-{}".format(int(time.time()), self.hashes['sha256'])

        self.report = {}
        self.new_processes = []
        self.ended_processes = []
        self.new_hashes = []
        self.deleted_hashes = []
        self.setup()

        self.log.info("> Report Dir: {}".format(self.report_dir))

    def setup(self):
        if not os.path.isdir(self.report_dir):
            os.mkdir(self.report_dir) #TODO: mkdir -p
        if not os.path.isdir(self.report_dir + "/files"):
            os.mkdir(self.report_dir + "/files") 

    def process_ps_results(self, ps1, ps2):
        s_ps1 = ps1.split('\n')
        s_ps2 = ps2.split('\n')
        for p_post in [i for i in s_ps2 if i not in s_ps1 ]:
            rec = p_post.lstrip().split(' ')
            self.new_processes.append(rec)

        for p_pre in [i for i in s_ps1 if i not in s_ps2 ]:
            rec = p_post.lstrip().split(' ')
            self.ended_processes.append(rec)


    def process_fs_results(self, s_fs1, s_fs2):
        for p_post in [i for i in s_fs2 if i not in s_fs1 ]:
            rec = p_post.lstrip().split("-", 1)
            self.new_hashes.append(rec)

        for p_pre in [i for i in s_fs1 if i not in s_fs2 ]:
            rec = p_pre.lstrip().split("-", 1)
            self.deleted_hashes.append(rec)


#        print(self.new_hashes)
#        print(self.deleted_hashes)

    def pull_new_files(self, disk_path):
        fList = []
        for f in self.new_hashes:
            fList.append(f[1])

        print("> Saving {} files".format(len(fList)))
        save_files(disk_path, fList, self.report_dir + "/files/")

    def generate_report(self):
        out = "DetuxNG Sandbox Execution Report\n"
        out += "Start: {} | End: {}\n".format(
            self.samplerun.starttime, 
            self.samplerun.endtime)
        out += "-----------------\n"
        out += "New Files\n"
        for new_file in self.new_hashes:
            out += " - [{}] {}\n".format(new_file[0], new_file[1])
        out += "Deleted Files"            
        for del_file in self.deleted_hashes:
            out += " - [{}] {}\n".format(del_file[0], del_file[1])




        with open(self.report_dir + "/report.txt", 'w') as w:
            w.write(out)

        with open(self.report_dir + "/report.json", 'w') as w:
            w.write(json.dumps({
                "files" : {
                    "new" : self.new_hashes,
                    "deleted": self.deleted_hashes},
                "processes" : {
                    "new" : self.new_processes,
                    "ended": self.ended_processes},
                "submitted": {
                    "hashes": self.hashes}
                }))













