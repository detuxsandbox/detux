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




class SandboxRun(object):
    def __init__(self, filepath, args, platform, os, timeout):
        self.log = new_logger("SandboxRun")

        self.filepath = filepath
        self.hashes = self.hashfile()
        self.args = args

        if platform == "auto":
            _ = self.identify_arch(filepath)
            self.filetype = _[0]
            self.platform = _[1]
            self.os = _[2]

        else:
            self.filetype = 'auto'
            self.platform = platform
            self.os = os


        self.starttime = None # When the sample started
        self.stoptime = None # When the sample stopped
        self.endtime = None # When the sample should stop

        self.timeout = timeout

    def get_exec_command(self):
        if self.os == "linux":
            return "chmod +x /sample && nohup /sample > /dev/null 2>&1 >> /var/log/runlog &"
        else:
            return "START /B /sample"


    def hashfile(self):
        return {
            "md5": hashlib.md5(open(self.filepath,'rb').read()).hexdigest(),
            "sha1": hashlib.sha1(open(self.filepath,'rb').read()).hexdigest(),
            "sha256": hashlib.sha256(open(self.filepath,'rb').read()).hexdigest()
        }

    def mark_start(self):
        self.starttime = int(time.time())
        self.endtime = self.starttime + self.timeout

    def mark_end(self):
        self.endtime = int(time.time())


    def identify_arch(self, filepath):
        m = Magic()
        filetype = ""
        try:
            filetype = m.from_file(filepath)
        except Exception as e:
            # certain version of libmagic throws error while parsing file, the CPU information is however included in the error in somecases
            filetype = str(e)
        if "Bourne-Again" in filetype:
            return filetype, "x64", "linux"

        if filetype.startswith("ELF"):
            if "64-bit" in filetype:
                return filetype, "x64", "linux"

        if filetype.startswith("PE32"):
            if "x86-64" in filetype:
                return filetype, "x64", "windows"
        return filetype, "UNK", "UNK"


class Hypervisor(object):
    def __init__(self, sconn='qemu:///system'):
        self.log = new_logger("Hypervisor")

        self.vms = {}
        self.dhcp = {}
        try:
            self.conn = libvirt.open(sconn)
            self.list_vms()
        except libvirt.libvirtError:
            self.log.error('Failed to open connection to the hypervisor')
            sys.exit(1)
        self.generate_dhcp_mapping()

    def list_vm_names(self):
        ret = []
        for _ in self.conn.listAllDomains():
            ret.append(_.name())

        return ret

    def list_vms(self):
        for _ in self.list_vm_names():
            vm = _.split("_")
            if vm[0] == "detuxng":
                self.vms[_] = VM(self, _ ,vm[1],vm[2], vm[3])

    def lookup(self, name):
        try:
            host = self.conn.lookupByName(name)
        except libvirt.libvirtError:
            self.log.error('Failed to find the main domain')
            return None
        return host

    def generate_dhcp_mapping(self):
        self.network_names = self.conn.listNetworks()
        for _ in self.network_names:
            net = self.conn.networkLookupByName(_)
            for lease in net.DHCPLeases():
#                self.log.debug(lease)
                self.dhcp[lease.get('mac', "UNKN")] = {
                    'ipaddr' : lease.get('ipaddr', "UNKN"),
                    'iface' : lease.get('iface', "UNKN"),
                    'clientid' : lease.get('clientid', "UNKN"),
                    'hostname' : lease.get('hostname', "UNKN"),
                }


class VM(Hypervisor):
    def __init__(self, hypervisor, name, arch, os, os_version):
        self.log = new_logger("Hypervisor_VM")
        self.hypervisor = hypervisor
        self.conn = self.hypervisor.conn
        self.name = name
        self.arch = arch
        self.os = os
        self.os_version = os_version
        self.ready = False
        self.ipaddr = False
        self.dhcp = False

        self.username = None
        self.password = None
        self.port = None
        self.drive_path = self.get_drive_path()

    def get_drive_path(self):
        self.handle = self.lookup(self.name)
        #<\'/var/lib/libvirt/images/detuxng_x64_ubuntu_2004.qcow2\'/
        for drive_path in re.search(r"<source file='(.+?)'", self.handle.XMLDesc()).groups(1):
            return drive_path

    def connect(self):
        self.handle = self.lookup(self.name)
        self.log.info(">> Connecting to : {}".format(self.name))
        self.poweron()
        time.sleep(5)
        # Wait for power-on
        while True:
            state, note = self.get_state()
            self.hypervisor.generate_dhcp_mapping()
            self.log.info(">>> Status: {} ({})".format(state, note))
            if state != 1:
                return False

            # Lookup IP address for machine
            for hwaddr in re.search(r"<mac address='([A-Za-z0-9:]+)'", self.handle.XMLDesc()).groups(1):
                if hwaddr in self.hypervisor.dhcp:
                    self.ipaddr = self.hypervisor.dhcp[hwaddr].get('ipaddr', False)
                    self.dhcp = self.hypervisor.dhcp[hwaddr]
                else:
                    self.log.error("Error case - sleep and retry")
                    continue
            # Break out if we have DHCP
            if self.dhcp == False or self.ipaddr == False:
                self.log.info("Waiting on network...")
                time.sleep(10)
            else:
                return True

        return True

    def restore_snapshot(self):
        self.handle.revertToSnapshot(self.handle.snapshotCurrent())

    def poweron(self):
#        print(self.get_state())
        self.restore_snapshot()
#        time.sleep(2)
        self.handle.create()
#        time.sleep(5)
        return True

    # Not working yet
    def shutdown(self):
        self.restore_snapshot()
        if self.get_state() == libvirt.VIR_DOMAIN_RUNNING:
            self.handle.shutdown()

    # Not working yet
    def reset(self):
        self.restore_snapshot()
        if self.get_state() == libvirt.VIR_DOMAIN_RUNNING:
            self.handle.shutdown()

    # 
    def reboot(self):
        self.handle.reboot()

    def get_state(self):
        note = ""
        state, reason = self.handle.state()
        if state == libvirt.VIR_DOMAIN_NOSTATE:
            note = 'VIR_DOMAIN_NOSTATE'
        elif state == libvirt.VIR_DOMAIN_RUNNING:
            note = 'VIR_DOMAIN_RUNNING'
        elif state == libvirt.VIR_DOMAIN_BLOCKED:
            note = 'VIR_DOMAIN_BLOCKED'
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            note = 'VIR_DOMAIN_PAUSED'
        elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
            note = 'VIR_DOMAIN_SHUTDOWN'
        elif state == libvirt.VIR_DOMAIN_SHUTOFF:
            note = 'VIR_DOMAIN_SHUTOFF'
        elif state == libvirt.VIR_DOMAIN_CRASHED:
            note = 'VIR_DOMAIN_CRASHED'
        elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            note = 'VIR_DOMAIN_PMSUSPENDED'
        else:
            note = 'Unknown'
        return state, note



