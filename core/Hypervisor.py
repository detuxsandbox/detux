#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import re
import sys
import time
import libvirt
from core.common import new_logger

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
        self.hwaddr = None        

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
                    self.hwaddr = hwaddr
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
        self.restore_snapshot()
        self.handle.create()
#        time.sleep(5)
        return True

    def shutdown(self):
        self.restore_snapshot()
        if self.get_state() == libvirt.VIR_DOMAIN_RUNNING:
            self.handle.shutdown()

    def reset(self):
        self.restore_snapshot()
        if self.get_state() == libvirt.VIR_DOMAIN_RUNNING:
            self.handle.shutdown()

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



