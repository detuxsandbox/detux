#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import libvirt
import sys

import logging

log = logging.getLogger("obj_hypervisor")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)    
log.addHandler(handler)
log.setLevel(logging.DEBUG)


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





if __name__ == "__main__":
    h = Hypervisor()
    dom0 = h.lookup("detuxng_x64_ubuntu_2004")

    print("Domain 0: id %d running %s" % (dom0.ID(), dom0.OSType()))


    print(dom0.info())
    dom0.reboot()
    print(dom0.info())
