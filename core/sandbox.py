#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission..


import time
import os
import random
from configparser import ConfigParser

from core.objects import Hypervisor



class Sandbox:
    def __init__(self, config_path):
        self.config = ConfigParser()
        self.config.read(config_path)
        self.default_cpu = self.config.get("detux", "default_cpu")
        self.debug = self.config.get("detux", "debug_log")

        self.sandboxes = {}
        self.load_mapping()


    def load_mapping(self):

        sandbox_list = self.config.get("mapping", "sandbox_list")
        for s in sandbox_list.replace(' ', '').split(','):
            self.sandboxes[s] = {
                'arch': self.config.get(s, 'arch'),
                'tags': self.config.get(s, 'tags').split(','),
                'username': self.config.get(s, 'username'),
                'password': self.config.get(s, 'password'),
                'os': self.config.get(s, 'os'),
            }

        print(self.sandboxes)

    def get_sandbox_by_arch(self, arch):
        opt = []
        for s in self.sandboxes:
            if self.sandboxes[s]['arch'] == arch:
                opt.append(s)
        return opt

    def execute(self, sample):
        sandbox_starttime = time.time()
        print(sample.platform)







