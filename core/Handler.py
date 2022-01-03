#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission..


import os
import time
import random
import paramiko

from core.common import new_logger



# Linux_SandboxHandler defines an object that handles interations with the sandbox using
# SSH (using paramiko).  This object will also hold basic introspection functionality.
class Linux_SandboxHandler(object):
    def __init__(self, host, port, username, password):
        self.log = new_logger("Linux_SandboxHandler")
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    # connect() establishes a connection to the sandbox using SSH and establish an SFTP 
    #  session.  There is a built in retry counter (limited to 5 attempts).  The 
    # resulting SSH handle is saved to self.ssh and the SFTP handle to self.sftp
    def connect(self):
        tries = 5
        e = None
        while tries > 0:
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())            
                self.ssh.connect(
                    self.host, 
                    port=self.port, 
                    username=self.username, 
                    password=self.password)
                self.sftp = self.ssh.open_sftp()
                return True     
            except Exception as e:
                self.log.error(e)
                tries -= 1
                time.sleep(10)
        #self.log.error(e)
        return False

    # exec() will run remote commands on the sandbox using ssh.
    def exec(self, commands, timeout=10, noprompt = False):
        result = None

        try:
            stdin, stdout, stderr  = self.ssh.exec_command(commands, timeout=timeout)
            result = "".join(stdout.readlines()+ stderr.readlines())
        except Exception as e:
            self.log.error(e)
            self.log.error("[+] Error in ssh_execute: %s {%s }" % (e, result))
            return None
        return result

    # upload() uploads a file using the sftp connection
    def upload(self, src_file, dst_file):
        try:
            self.sftp.put(src_file, dst_file)
            return True
        except Exception as e:
            self.log.error("[+] Error in scp: %s" % (e,)   )
            return False
        return False

    # download() downloads a file using the sftp connection
    def download(self, src_file, dst_file):
        try:
            self.sftp.get(src_file, dst_file)
            return True
        except Exception as e:
            self.log.error("[+] Error in scp: %s" % (e,)   )

        return False        

    # list_procs() will run a "ps faux" on the running system to obtain
    #  a list of running processes
    def list_procs(self):
        try:
            return self.exec("ps -Ao pid,comm")
        except Exception as e:
            self.log.error("[+] Error in listproc: %s" % (e,)   )

        return False