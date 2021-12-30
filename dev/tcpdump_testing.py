#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import os
import re
import sys
import time
import libvirt
import logging
import threading
import subprocess
import signal




class PCAPHandler(object):
    def __init__(self, interval=1):
        self.run()

    def run(self):
        cmd = "tcpdump -nn -i {INTERFACE} -w {REPORT_PCAP}".format(INTERFACE="virbr0", REPORT_PCAP="./test.pcap")
        self.handle = subprocess.Popen(cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,             
            preexec_fn=os.setsid
            )

    def stop(self):
        os.killpg(os.getpgid(self.handle.pid), signal.SIGTERM)
        #self.handle.kill()

if __name__ == "__main__":
    p = PCAPHandler()
#    p.run()


