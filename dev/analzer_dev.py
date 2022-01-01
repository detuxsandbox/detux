#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import os
import re
import sys
import guestfs

class HostAnalzer_Linux(object):
    def __init__(self, drivepath):
        self.g = guestfs.GuestFS(python_return_dict=True)
        self.g.add_drive_opts(drivepath, readonly=1)
        self.g.launch()

        self.roots = self.g.inspect_os()
        if len(self.roots) == 0:
            print("inspect_vm: no operating systems found", file=sys.stderr)
            sys.exit(1)

        for root in self.roots:
            mps = self.g.inspect_get_mountpoints(root)
            for device, mp in sorted(mps.items(), key=lambda k: len(k[0])):
                try:
                    self.g.mount_ro(mp, device)
                except RuntimeError as msg:
                    print("%s (ignored)" % msg)

    def get_root_info(self):
        for root in self.roots:
            print("Root device: %s" % root)

            print("  Product name: %s" % (self.g.inspect_get_product_name(root)))
            print("  Version:      %d.%d" %
                  (self.g.inspect_get_major_version(root),
                   self.g.inspect_get_minor_version(root)))
            print("  Type:         %s" % (self.g.inspect_get_type(root)))
            print("  Distro:       %s" % (self.g.inspect_get_distro(root)))


    def run(self):
            filename = posix_path("/etc/issue.net")
            if self.g.is_file(filename):
                print("--- %s ---" % filename)
                lines = self.g.head_n(3, filename)
                for line in lines:
                    print(line)

    def hash_filesystem(self):
        print("Hashing FS")
        last = ""
        f = ""
        out = []
        counter = 0
        for _ in self.g.find("/"):
            counter += 1
            f = "/" + _
            if self.g.is_file(f):
                try:
                    out.append("{} - {}".format(self.g.checksum("md5", posix_path(f)), f))
                except Exception as e:
                    print(e)
                    print(f)
                    return

        print("Done")

    def close(self):
        self.g.umount_all()

def posix_path(*segments):
    return re.sub('^[a-zA-Z]:', '', os.path.join(*segments)).replace('\\', '/')


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("inspect_vm: missing disk image to inspect", file=sys.stderr)
        sys.exit(1)
    disk = sys.argv[1]

    h = HostAnalzer_Linux(disk)
    #h.get_root_info()
    h.hash_filesystem()
    h.close()

