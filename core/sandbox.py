# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

import pexpect
import paramiko
import time
from ConfigParser import ConfigParser
from hashlib import sha256
from magic import Magic
import os
import random

class Sandbox:
    def __init__(self, config_path):
        self.config = ConfigParser()
        self.config.read(config_path)
        self.default_cpu = self.config.get("detux", "default_cpu")
        
    def execute(self, binary_filepath, platform, sandbox_id, interpreter = None):
        sandbox_starttime = time.time()
        sandbox_endtime   = sandbox_starttime
        vm_exec_time = self.config.getint("detux", "vm_exec_time")
        qemu_command = self.qemu_commands(platform, sandbox_id) 
        pcap_folder = self.config.get("detux", "pcap_folder")
        if not os.path.isdir(pcap_folder):
            os.mkdir(pcap_folder)
        ssh_host = self.config.get(platform+"-"+sandbox_id, "ip")
        ssh_user = self.config.get(platform+"-"+sandbox_id, "user")
        macaddr  = self.config.get(platform+"-"+sandbox_id, "macaddr")
        ssh_password = self.config.get(platform+"-"+sandbox_id, "password")
        ssh_port  = self.config.getint(platform+"-"+sandbox_id, "port")
        pcap_command = "/usr/bin/dumpcap -i %s -P -w %s -f 'not ((tcp dst port %d and ip dst host %s) or (tcp src port %d and ip src host %s))'"
        # A randomly generated sandbox filename       
        dst_binary_filepath = "/tmp/" + ("".join(chr(random.choice(xrange(97,123))) for _ in range(random.choice(range(6,12)))))
        sha256hash = sha256(open(binary_filepath, "rb").read()).hexdigest()
        interpreter_path = { "python" : "/usr/bin/python", "perl" : "/usr/bin/perl", "sh" : "/bin/sh", "bash" : "/bin/bash"  }
        if qemu_command == None :
            return {}
        qemu_command += " -net nic,macaddr=%s -net tap -monitor stdio" % (macaddr,)  
        print qemu_command    
        qemu = pexpect.spawn(qemu_command)
        try: 
            qemu.expect("(qemu).*")
            qemu.sendline("info network")
            qemu.expect("(qemu).*")
            ifname =  qemu.before.split("ifname=", 1)[1].split(",", 1)[0]
            qemu.sendline("loadvm init")
            qemu.expect("(qemu).*")


            pre_exec  = {}
            post_exec = {}
            #pre_exec  = self.ssh_execute(ssh_host, ssh_port, ssh_user, ssh_password, ["netstat -an", "ps aux"])
            # Move the binary
            self.scp(ssh_host, ssh_port, ssh_user, ssh_password, binary_filepath, dst_binary_filepath)
            # Pre binary execution commands
            pre_exec  = self.ssh_execute(ssh_host, ssh_port, ssh_user, ssh_password, ["chmod +x %s" % (dst_binary_filepath,)])

            # Start Packet Capture
            pcap_filepath = os.path.join(pcap_folder, "%s_%d.cap" %(sha256hash,time.time(),))
            pcapture = pexpect.spawn(pcap_command % (ifname, pcap_filepath, ssh_port, ssh_host, ssh_port, ssh_host))

            # wait for pcapture to start and then Execute the binary
            time.sleep(5)
            command_to_exec = dst_binary_filepath if interpreter == None else "%s %s" % (interpreter_path[interpreter], dst_binary_filepath,)
            print "[+] Executing %s" % (command_to_exec,)
            exec_ssh = self.ssh_execute(ssh_host, ssh_port, ssh_user, ssh_password, command_to_exec, True, False )
            starttime = time.time()
            while  time.time() < starttime + vm_exec_time:
                if not qemu.isalive():
                    vm_exec_time = 0
            if qemu.isalive():
                # Post binary execution commands
                post_exec = self.ssh_execute(ssh_host, ssh_port, ssh_user, ssh_password, ["ps aux"])
                try:
                    if exec_ssh <> None:
                        exec_ssh.close()
                except Exception as e:
                    print "[+] Error while logging out exec_ssh: %s" % (e,)            
                qemu.sendline("q")
           
            # Stop Packet Capture
            if pcapture.isalive():
                pcapture.close()

            sandbox_endtime = time.time()
            result = {'start_time' : sandbox_starttime, 'end_time' : sandbox_endtime, 'pcap_filepath' : pcap_filepath}
            result['post_exec_result'] = post_exec
            result['cpu_arch'] = platform
            result['interpreter'] = interpreter
        except Exception as e:
            print "[-] Error:", e
            if qemu.isalive():
                qemu.close()
            return {}
        
        return result

        
    def identify_platform(self, filepath):
        filemagic = Magic()
        filetype = ""
        try:
            filetype = filemagic.id_filename(filepath)
        except Exception as e:
            # certain version of libmagic throws error while parsing file, the CPU information is however included in the error in somecases
            filetype = str(e)
#        filemagic.close()
        if "ELF 32-bit" in filetype: 
            if "ARM" in filetype:
                return "ELF", "arm"
            if "80386" in filetype:
                return "ELF", "x86"
            if ("MIPS" in filetype) and ("MSB" in filetype):
                return "ELF", "mips"
            if "MIPS" in filetype:
                return "ELF", "mipsel"
            if "PowerPC" in filetype:
                return "ELF", "powerpc"
        if "ELF 64-bit" in filetype:
            if "x86-64" in filetype:
                return "ELF", "x86-64"


        return filetype, self.default_cpu


    def qemu_commands(self, platform, sandbox_id):
        if platform == "x86":
            return "sudo qemu-system-i386 -hda qemu/x86/%s/debian_wheezy_i386_standard.qcow2 -vnc 127.0.0.1:1%s" % (sandbox_id, sandbox_id, )
        if platform == "x86-64":
            return "sudo qemu-system-x86_64 -hda qemu/x86-64/%s/debian_wheezy_amd64_standard.qcow2 -vnc 127.0.0.1:2%s" % (sandbox_id, sandbox_id,)
        if platform == "mips":
            return 'sudo qemu-system-mips -M malta -kernel qemu/mips/%s/vmlinux-3.2.0-4-4kc-malta -hda qemu/mips/%s/debian_wheezy_mips_standard.qcow2 -append "root=/dev/sda1 console=tty0" -vnc 127.0.0.1:3%s'  % (sandbox_id, sandbox_id, sandbox_id,)
        if platform == "mipsel":
            return 'sudo qemu-system-mipsel -M malta -kernel qemu/mipsel/%s/vmlinux-3.2.0-4-4kc-malta -hda qemu/mipsel/%s/debian_wheezy_mipsel_standard.qcow2 -append "root=/dev/sda1 console=tty0" -vnc 127.0.0.1:4%s'  % (sandbox_id, sandbox_id, sandbox_id, )
        if platform == "arm":
            return 'sudo qemu-system-arm -M versatilepb -kernel qemu/arm/%s/vmlinuz-3.2.0-4-versatile -initrd qemu/arm/%s/initrd.img-3.2.0-4-versatile -hda qemu/arm/%s/debian_wheezy_armel_standard.qcow2 -append "root=/dev/sda1" -vnc 127.0.0.1:5%s'  % (sandbox_id, sandbox_id, sandbox_id, sandbox_id,)
        return None


    def ssh_execute(self, host, port, user, password, commands, noprompt = False, logout = True):
        result = None
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port=port, username=user, password=password)
            if type(commands) == type(str()):
                stdin, stdout, stderr  = ssh.exec_command(commands, timeout=10)
                if noprompt == False:    
                    result = "".join(stdout.readlines())
            if type(commands) == type(list()):
                result = {}
                for command in commands:
                    stdin, stdout, stderr  = ssh.exec_command(command, timeout=10)
                    result[command] = "".join(stdout.readlines())
            if logout:
                ssh.close()
            else:
                return ssh # Return SSH object to logout later
        except Exception as e:
            print "[+] Error in ssh_execute: %s" % (e,)
        return result

    def scp(self, host, port, user, password, src_file, dst_file):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port=port, username=user, password=password)
            sftp = ssh.open_sftp()
            sftp.put(src_file, dst_file)
        except Exception as e:
            print "[+] Error in scp: %s" % (e,)        

         
