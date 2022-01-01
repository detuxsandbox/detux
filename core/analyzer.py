#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import sys
import guestfs

from core.common import new_logger


class HostAnalzer_Linux(object):
    def __init__(self, drivepath):
        self.log = new_logger("Report")

        self.g = guestfs.GuestFS(python_return_dict=True)
        self.g.add_drive_opts(drivepath, readonly=1)
        self.g.launch()

        self.roots = self.g.inspect_os()
        if len(self.roots) == 0:
            self.log.error("inspect_vm: no operating systems found", file=sys.stderr)
            sys.exit(1)

        for root in self.roots:
            mps = self.g.inspect_get_mountpoints(root)
            for device, mp in sorted(mps.items(), key=lambda k: len(k[0])):
                try:
                    self.g.mount_ro(mp, device)
                except RuntimeError as msg:
                    self.log.error("%s (ignored)" % msg)

    def get_root_info(self):
        for root in self.roots:
            self.log.info("Root device: %s" % root)

            self.log.info("  Product name: %s" % (self.g.inspect_get_product_name(root)))
            self.log.info("  Version:      %d.%d" %
                  (self.g.inspect_get_major_version(root),
                   self.g.inspect_get_minor_version(root)))
            self.log.info("  Type:         %s" % (self.g.inspect_get_type(root)))
            self.log.info("  Distro:       %s" % (self.g.inspect_get_distro(root)))


    def run(self):
            filename = "/etc/issue.net"
            if self.g.is_file(filename):
                self.log.debug("--- %s ---" % filename)
                lines = self.g.head_n(3, filename)
                for line in lines:
                    self.log.debug(line)

    def hash_filesystem(self):
        self.log.info("> Hashing FS")
        fs = []
        for _ in self.g.find("/"):
            f = "/" + _
            if self.g.is_file(f):
                fs.append("{}-{}".format(self.g.checksum("md5", f), f))
                
        return fs

    def close(self):
        self.g.umount_all()

def get_file(disk_path, filename):
    h = HostAnalzer_Linux(disk_path)
    fdata = None
    if h.g.is_file(filename):
        h.log.info("> Fetching %s" % filename)
        fdata = h.g.read_file(filename)
    h.close()
    return fdata

def save_files(disk_path, fList, folderPath):
    h = HostAnalzer_Linux(disk_path)
    fdata = None
    print(folderPath)
    for filename in fList:
        if h.g.is_file(filename):
            h.log.info("> Fetching %s - (%s)" % (filename, folderPath + filename.replace('/', "_")))
            with open(folderPath + filename.replace('/', "_"), "wb") as w:
                w.write(h.g.read_file(filename))
    h.close()
    return fdata



def hash_filesystem(disk_path):
    h = HostAnalzer_Linux(disk_path)
    fs = h.hash_filesystem()
    h.close()
    return fs

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("inspect_vm: missing disk image to inspect", file=sys.stderr)
        sys.exit(1)
    disk = sys.argv[1]

