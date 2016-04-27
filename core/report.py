# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

from hashlib import md5, sha256, sha1
import json
import magic
from magic import Magic
from sandbox import Sandbox
from packetparser import PacketParser
import os
from datetime import datetime
import uuid

class Report:
    def __init__(self, sample_filepath, sandbox_result):
        self.cpu_arch = sandbox_result['cpu_arch']
        self.interpreter = sandbox_result['interpreter']
        self.sample_filepath = sample_filepath
        self.pcap_filepath = sandbox_result['pcap_filepath']
        self.post_exec_result = sandbox_result['post_exec_result']
        self.start_time = sandbox_result['start_time']
        self.end_time = sandbox_result['end_time']
        self.error_in_exec = True if sandbox_result == {} else False
        self.report = {}
        

    def add_tags(self, tags):
        self.report['tag'] = tags

    def static_analysis(self):
        analysis_commands = { 
                        'readelf' : "readelf -a %s",
                        'strings' : "strings %s"
                       }

        static_report = {}
        try:

            for cmd_name, cmd in analysis_commands.items():
                static_report[cmd_name] = unicode(os.popen(cmd % (self.sample_filepath,)).read(), errors='replace')

        except Exception as e:
            pass
        return static_report

    def get_report(self):
        sample_file = open(self.sample_filepath, "rb")
        sample_data = sample_file.read()
        sample_file.close()
        self.report['md5'] = md5(sample_data).hexdigest()
        self.report['sha256'] = sha256(sample_data).hexdigest()
        self.report['sha1'] = sha1(sample_data).hexdigest()
        self.report['filesize'] = len(sample_data)
        network_con2 = {}
        ip = set()
        port = set()
        protocol = set()
        dns = set()
        try:
            filemagic = Magic()
            self.report['filetype'] = filemagic.id_filename(self.sample_filepath)
#            filemagic.close()
        except Exception as e:
            self.report['filetype'] = "Unknown"
        if self.error_in_exec == False and os.path.isfile(self.pcap_filepath):
            self.report['cpu'] = self.cpu_arch
            self.report['interpreter'] = self.interpreter
            pparser = PacketParser(self.pcap_filepath)
            self.report['dns_request'] = pparser.get_dns_requests()
            self.report['url'] = pparser.get_urls()
            network_con = pparser.get_network_connections()
            for dns_q in self.report['dns_request']:
                dns.add(dns_q['name'])
                if dns_q['type'] == "A":
                    ip.add(dns_q['result'])
            for key in network_con.keys():
                protocol.add(key)
                network_con[key] = list(network_con[key])
                if key in ['TCP', 'UDP']:
                    network_con2[key] = []
                    for socks in network_con[key]:
                        socks = socks.split(" : ")
                        network_con2[key].append( {'ip': socks[0], 'port' : socks[1]} )
                        ip.add(socks[0])
                        port.add(socks[1])
                else:
                    network_con2[key] = network_con[key]
                    for t_ip in network_con[key]:
                        ip.add(t_ip)
        self.report['network'] = network_con2
        self.report['dns'] = list(dns)
        self.report['ip'] = list(ip)
        self.report['port'] = list(port)
        self.report['protocol'] = list(protocol)
        self.report['static_analysis'] = self.static_analysis()   
        self.report['start_time'] = datetime.utcfromtimestamp(self.start_time).isoformat()
        self.report['end_time'] = datetime.utcfromtimestamp(self.end_time).isoformat()
        self.report['sample_filepath'] = self.sample_filepath
        self.report['pcap_filepath'] = self.pcap_filepath 
        self.report['error'] = self.error_in_exec      
        return self.report
