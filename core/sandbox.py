#!/usr/bin/env python3
# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission..


import os
import time
import random
import paramiko

from configparser import ConfigParser
from core.objects import Hypervisor
from core.report import PCAPHandler
from core.analyzer import hash_filesystem

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
            self.log.error("[+] Error in ssh_execute: %s" % (e,))
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

# Sandbox defines the core object of DetuxNG.  
class Sandbox:
    def __init__(self, config_path, hypervisor):
        self.log = new_logger("Sandbox")        
        self.config = ConfigParser()
        self.config.read(config_path)

        self.hypervisor = hypervisor

        self.sandboxes = {}
        self.load_mapping()


    def load_mapping(self):
        sandbox_list = self.config.get("mapping", "sandbox_list")
        for s in sandbox_list.replace(' ', '').split(','):
            sandbox_config = self.config[s] 
            self.sandboxes[s] = {
                'arch': sandbox_config.get('arch', ""),
                'tags': sandbox_config.get('tags', []).split(','),
                'username': sandbox_config.get('username', ""),
                'password': sandbox_config.get('password', ""),
                'env': sandbox_config.get('env', ""),
            }
            #If value missing:
            if sandbox_config.get('port', True):
                self.sandboxes[s]['port'] = 22
            else:
                self.sandboxes[s]['port'] = sandbox_config.get('port')


        return True

    def get_environment_by_arch(self, arch):
        opt = []
        for s in self.sandboxes:
            if self.sandboxes[s]['arch'] == arch:
                opt.append(s)
        return opt

    def select_environment(self, sample):
        opt = []
        for s in self.sandboxes:
            if self.sandboxes[s]['arch'] == sample.platform and self.sandboxes[s]['env'] == sample.os:
                if s in self.hypervisor.vms.keys():
                    self.hypervisor.vms[s].username = self.sandboxes[s]['username']
                    self.hypervisor.vms[s].password = self.sandboxes[s]['password']                    
                    self.hypervisor.vms[s].port = self.sandboxes[s]['port']
                    self.hypervisor.vms[s].env = self.sandboxes[s]['env']


                    opt.append(self.hypervisor.vms[s])
        return opt        

    def run(self, sample, results):
        self.log.info("> Starting... ")

        target_env = None
        target_env_list = self.select_environment(sample)
        for target_env in target_env_list:
            target_env.restore_snapshot()
            start_disk_hashes = hash_filesystem(target_env.drive_path)

            res = target_env.connect()


            # TODO: Testing
            if res == False:
                self.log.error("X Unable to setup {}".format(target_env.name))
                target_env.ready = False
                # Continue - Loop to try and different system
            else:
                target_env.ready = True
                break

        self.log.info("> Run in: {} (arch: {}, os: {}, ip: {}) ".format(
            target_env.name, 
            target_env.arch, 
            target_env.os,
            target_env.ipaddr))

        if target_env.env == "linux" or target_env.os == "windows":
            self.log.info(">> Starting connection test")
            conn = Linux_SandboxHandler(
                target_env.ipaddr, 
                target_env.port,
                target_env.username,
                target_env.password)

            connected = conn.connect()

            if conn.exec("whoami") == None:
                # Need to close connections
                return False

        elif target_env.os == "windows":
            self.log.error("TODO: windows")
            return False

        ## Start Network Capture
        ph = PCAPHandler(results, target_env)
        ph.start()

        # Start Sandboxing.  List processes before start, upload sample, mark executabe and 
        #  call conn.exec() to run the sample
        self.log.info("> Go Time!")
        start_ps = conn.list_procs()
        conn.upload(sample.filepath, "/sample")

        # TODO - Don't rely on timeout
        sample.mark_start()
        conn.exec(sample.get_exec_command())

        while sample.endtime > int(time.time()):
            time.sleep(1)
        self.log.info("> Runtime finished")

        # Start Cleanup.  Shutdown sandbox, Mark execution completion time, stop network logging and download runlog
        sample.mark_end()
        ph.stop()

        self.log.info("> Processing process diff")
#        results.process_ps_results(start_ps, conn.list_procs())

        self.log.info("> Processing file system diff")
        results.process_fs_results(start_disk_hashes, hash_filesystem(target_env.drive_path))

        self.log.info("> Pulling new files")
        results.pull_new_files(target_env.drive_path)


        self.log.info("> Finished Execution")
        target_env.shutdown()
        target_env.reset()
        results.generate_report()

