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
from core.objects import Hypervisor, PCAPHandler



class Linux_SandboxHandler(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
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
            print(e)
            return False

    def exec(self, commands, timeout=10, noprompt = False):
        result = None

        try:
            stdin, stdout, stderr  = self.ssh.exec_command(commands, timeout=timeout)
            result = "".join(stdout.readlines()+ stderr.readlines())
        except Exception as e:
            print(e)
            print("[+] Error in ssh_execute: %s" % (e,))
            return None
        return result

    def upload(self, src_file, dst_file):
        try:
            self.sftp.put(src_file, dst_file)
            return True
        except Exception as e:
            print("[+] Error in scp: %s" % (e,)   )

        return False

    def download(self, src_file, dst_file):
        try:
            self.sftp.get(src_file, dst_file)
            return True
        except Exception as e:
            print("[+] Error in scp: %s" % (e,)   )

        return False        

    def list_procs(self):
        try:
            return self.exec("ps faux")
        except Exception as e:
            print("[+] Error in listproc: %s" % (e,)   )

        return False


class Sandbox:
    def __init__(self, config_path, hypervisor):
        self.config = ConfigParser()
        self.config.read(config_path)

        self.hypervisor = hypervisor

        self.default_cpu = self.config.get("detux", "default_cpu")
        self.debug = self.config.get("detux", "debug_log")

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
                if self.sandboxes[s]['env'] == "linux":
                    self.sandboxes[s]['port'] = 22

                elif self.sandboxes[s]['env'] == "windows":
                    self.sandboxes[s]['port'] = 445
                else:
                    continue
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
        print("> Starting... ")

        target_env = None
        target_env_list = self.select_environment(sample)
        for target_env in target_env_list:
            res = target_env.connect()

            # TODO: Testing
            if res == False:
                print("X Unable to setup ", target_env.name)
                target_env.ready = False
            else:
                target_env.ready = True
                break


        print("> Run in: {} (arch: {}, os: {}, ip: {}) ".format(
            target_env.name, 
            target_env.arch, 
            target_env.os,
            target_env.ipaddr))

        if target_env.env == "linux":
            print(">> Starting connection test")
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
            print("TODO")

        ## Start Network Capture
        ph = PCAPHandler()
        return






        ### Start Sandboxing
        print("> Go Time!")
        start_ps = conn.list_procs()

        conn.upload(sample.filepath, "/sample")
        conn.exec("chmod +x /sample")

        # TODO - Don't rely on timeout
        print("START!")
        sample.start()
        conn.exec("nohup /sample > /dev/null 2>&1 >> /var/log/runlog &")
        print("STARTED!")

        while sample.endtime > int(time.time()):
            time.sleep(1)

        print("Stopped!")
        sample.stop()
        print(results.execution_log)
        conn.download("/var/log/runlog", "{}/runlog".format(results.report_dir))


        end_ps = conn.list_procs()
