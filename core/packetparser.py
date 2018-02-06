# Copyright (c) 2015 Vikas Iyengar, iyengar.vikas@gmail.com (http://garage4hackers.com)
# Copyright (c) 2016 Detux Sandbox, http://detux.org
# See the file 'COPYING' for copying permission.

import dpkt
import sys
from netaddr import *
import socket
import string 

class PacketParser:
    def __init__(self, pcap_filepath):
        self.pcap_filepath = pcap_filepath

    def load_pcap(self):
        self.pcap = dpkt.pcap.Reader(open(self.pcap_filepath, "rb"))

    def get_network_connections(self,protocols = ['TCP','UDP','ICMP'],unwanted_ip = ['0.0.0.0','255.255.255.255']):
        self.load_pcap()
        cnt = 0
        ip_list = {}
        try:

            for timestamp, buf in self.pcap:
                try:
                    cnt +=1
                    if buf == '\x00\x00\x00\x00':
                        #Some pcap files have bytes 00 in beginning, just discard them
                        continue
                    eth = dpkt.ethernet.Ethernet(buf)
                    ip = eth.data
                    ip_proto = ip.data
                    if ip_proto.__class__.__name__ not in protocols:
                        continue
                    if not ip_list.has_key(ip_proto.__class__.__name__):
                        ip_list[ip_proto.__class__.__name__] = set()
                    srcip = IPAddress(socket.inet_ntoa(ip.src))
                    dstip = IPAddress(socket.inet_ntoa(ip.dst))
                    if (srcip.format() not in ip_list) and (srcip.is_unicast() and not srcip.is_private()) and (srcip.format() not in unwanted_ip):
                        if ip_proto.__class__.__name__ in ['TCP', 'UDP']:
                            ip_list[ip_proto.__class__.__name__].add("%s : %s" % (srcip.format(),ip_proto.sport))
                        else:
                            ip_list[ip_proto.__class__.__name__].add(srcip.format())
                    if (dstip.format() not in ip_list) and (dstip.is_unicast() and not dstip.is_private()) and (dstip.format() not in unwanted_ip):
                        if ip_proto.__class__.__name__ in ['TCP', 'UDP']:
                            ip_list[ip_proto.__class__.__name__].add("%s : %s" % (dstip.format(),ip_proto.dport,))
                        else:
                            ip_list[ip_proto.__class__.__name__].add(dstip.format())   
                except Exception as e:
                    print "[+] Error in get_public_IPs: %s" % (e,) 
        except Exception as e:
            print "[+] Error in get_public_IPs: %s" % (e,) 

        return ip_list

    def get_urls(self ,protocols = ['TCP'],http_ports = [80, 8080, 8000]):
        self.load_pcap()
        cnt = 0
        #Initialisation of output variable lists
        urls = []
        try:
            for timestamp, buf in self.pcap:
                #Some times buf contains \x00 so this checks skip them 
                cnt +=1
                if buf == '\x00\x00\x00\x00':

                    #Some pcap files have bytes 00 in beginning, just discard them
                    continue
                else:
                    eth = dpkt.ethernet.Ethernet(buf)
                    ip = eth.data
                    tcp = ip.data
                    if tcp.__class__.__name__ in protocols:
                            if len(tcp.data) > 0:      
                                try:
                                    http = dpkt.http.Request(tcp.data)
                                    tcp_port = ":" + str(tcp.dport)
                                    url_host = http.headers['host'] + tcp_port  if tcp_port not in http.headers['host'] else http.headers['host']

                                    urls.append(unicode(url_host + http.uri, errors='replace'))
                                except Exception as e:
                                    pass
                                    #print "[-] Some error occured. - %s" % str(e)

        except Exception as e:
            print "[-] Error in geturl() : %s " % (e,)
        return urls

    def get_dns_requests(self,protocols = ['TCP','UDP']):
        self.load_pcap()
        cnt = 0
        dns_list = []
        try:
            for timestamp, buf in self.pcap:
                try:
                    #Some times buf contains \x00 so this checks skip them 
                    cnt +=1
                    if buf == '\x00\x00\x00\x00':
                        #Some pcap files have bytes 00 in beginning, just discard them
                        continue
                    else:
                        eth = dpkt.ethernet.Ethernet(buf)
                        ip = eth.data
                        tcp = ip.data

                        if tcp.__class__.__name__ in protocols:
                            if tcp.sport == 53 or tcp.dport == 53:
                                if eth.type == 2048 and ip.p == 17 :
                                    try:
                                        dns = dpkt.dns.DNS(tcp.data)
                                    except:
                                        #print "Error:DNS"
                                            continue # Discard errornous Data
                                    if dns.qr == dpkt.dns.DNS_R and dns.opcode == dpkt.dns.DNS_QUERY and dns.rcode == dpkt.dns.DNS_RCODE_NOERR:
                                        if len(dns.an) >= 1:
                                            for answer in dns.an:
                                                req = { }
                                                if answer.type == 1: #DNS_A
                                                    req = {'type': 'A', 'name': unicode(answer.name, errors='replace'),'result': socket.inet_ntoa(answer.rdata)}
                                                elif answer.type == 5:  # "CNAME request"
                                                    req = {'type': 'CN', 'name': unicode(answer.name, errors='replace'),'result': unicode(answer.cname, errors='replace')}
                                                elif answer.type == 12:
                                                         #print "PTR request", answer.name, "\tresponse", answer.ptrn
                                                    req = {'type': 'PTR', 'name': unicode(answer.name, errors='replace'),'result': unicode(answer.ptrname, errors='replace')}
                                                if req <> {} : dns_list.append(req)
                except Exception as e:
                    print "[-] Error in get_dns_request() : %s " % (e,) 
        except Exception as e:
            print "[-] Error in get_dns_request() : %s " % (e,)           
        return dns_list    


if __name__ == "__main__":
    if len(sys.argv)==2:
        import os.path
        if os.path.isfile(sys.argv[1]):
            pparse = PacketParser(sys.argv[1])
            print pparse.get_urls()
            print pparse.get_dns_requests()
            print pparse.get_network_connections()
    else:
        print "Usage: packetparser.py mypcapcapture.pcap"
