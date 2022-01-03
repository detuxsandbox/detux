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
import signal
import subprocess

import hashlib
from magic import Magic

from core.common import new_logger

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
