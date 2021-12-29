#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import libvirt
import sys
from magic import Magic

import logging

log = logging.getLogger("objects")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)    
log.addHandler(handler)
log.setLevel(logging.DEBUG)


class SandboxRun(object):
    def __init__(self, filepath, args, platform, timeout):
        self.filepath = filepath
        self.args = args

        if platform == "auto":
            _ = self.identify_platform(filepath)
            self.filetype = _[0]
            self.platform = _[1]
        else:
            self.filetype = 'auto'
            self.platform = platform

        self.starttime = None
        self.endtime = None
        self.timeout = timeout



    def identify_platform(self, filepath):
        m = Magic()
        filetype = ""
        try:
            filetype = m.from_file(filepath)
        except Exception as e:
            # certain version of libmagic throws error while parsing file, the CPU information is however included in the error in somecases
            filetype = str(e)
        if "Bourne-Again" in filetype:
            return filetype, "x64"

        if filetype.startswith("ELF"):
            if "64-bit" in filetype:
                return filetype, "x64"




        return filetype, "UNK"


class Hypervisor(object):
    def __init__(self, sconn='qemu:///system'):
        try:
            self.conn = libvirt.open(sconn)
        except libvirt.libvirtError:
            log.error('Failed to open connection to the hypervisor')
            sys.exit(1)     
    def lookup(self, name):
        try:
            host = self.conn.lookupByName(name)
        except libvirt.libvirtError:
            log.error('Failed to find the main domain')
            return None
        return host

    def restore_snapshot(self):
        dom0.revertToSnapshot(dom0.snapshotCurrent())





