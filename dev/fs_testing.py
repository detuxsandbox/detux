#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import libvirt
import filesystem
import sys

import guestfs

if len(sys.argv) < 3:
    print("inspect_vm: missing disk image to inspect", file=sys.stderr)
    sys.exit(1)
disk = sys.argv[1]

f = filesystem.FileSystem(disk)
f.mount(readonly=False)


import filesystem
f = filesystem.FileSystem('/var/lib/libvirt/images/detuxng_x64_ubuntu_2004.qcow2')
f.mount(readonly=False)
f.download('/etc/passwd', './testpas')

