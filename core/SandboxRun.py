#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import time

import hashlib
import magic

from core.common import new_logger


class SandboxRun(object):
    def __init__(self, args):
        self.log = new_logger("SandboxRun")

        self.filepath = args.sample_path
        self.hashes = self.hashfile()
        self.args = args
        self.timeout = args.timeout

        if args.cpu == "auto":
            _ = self.identify_arch(self.filepath)
            self.filetype = _[0]
            self.platform = _[1]
            self.os = _[2]

        else:
            self.filetype = 'auto'
            self.platform = args.cpu
            self.os = args.os


        self.starttime = None # When the sample started
        self.stoptime = None # When the sample stopped
        self.endtime = None # When the sample should stop


        self.print_info()

    def print_info(self):
        self.log.info("> Processing: {}".format(self.filepath))
        self.log.info("> Timeout: {}".format(self.timeout))
        self.log.info("> Platform: {}".format(self.platform))
        self.log.info("> OS: {}\n".format(self.os))


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
        m = magic.Magic()
        filetype = ""
        try:
            filetype = m.from_file(filepath)
        except Exception as e:
            filetype = str(e)

        if "Bourne-Again" in filetype:
            return filetype, "x64", "linux"

        if filetype.startswith("ELF"):
            if "64-bit" in filetype:
                return filetype, "x64", "linux"
            return filetype, "x64", "linux"

        if filetype.startswith("PE32"):
            if "x86-64" in filetype:
                return filetype, "x64", "windows"
            return filetype, "x64", "windows"

        return filetype, "UNK", "UNK"
