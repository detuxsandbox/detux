#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import libvirt
import sys

try:
    conn = libvirt.openReadOnly(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    sys.exit(1)

try:
    dom0 = conn.lookupByName("Domain-0")
except libvirt.libvirtError:
    print('Failed to find the main domain')
    sys.exit(1)

print("Domain 0: id %d running %s" % (dom0.ID(), dom0.OSType()))
print(dom0.info())
