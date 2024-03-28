import json
import os
from shutil import rmtree

CONFIG_PATH = 'configReseau.json'
EXPORT_PATH = 'exportConfig\\'

class AddressFamily:
    def __init__(self, name, address_family_json, redistribute_connected=False, send_community=False):
        self.name = name
        self.members = address_family_json
        self.redistribute_connected=redistribute_connected
        self.send_community=send_community
    
    def export(self):
        to_send=f" address-family {self.name}\n"
        if self.redistribute_connected:
            to_send+="  redistribute-connected\n"
        for member in self.members:
            if member.get("remote-as","")!="":
                to_send+=f"  neighbor {member['neighbor-address']} remote-as {member['remote-as']}\n"
            if member.get("update-source","")!="":
                to_send+=f"  neighbor {member['neighbor-address']} update-source {member['update-source']}\n"
            to_send+=f"  neighbor {member['neighbor-address']} activate\n"
            if self.send_community:
                to_send+= f"  neighbor {member['neighbor-address']} send-community extended\n"
        to_send+=" exit-address-family\n"
        return to_send


class VRF:
    def __init__(self, vrf_json):
        self.raw_json = vrf_json
        self.interfaces = []
        self.address_familys=[]

        self.load()
    
    def load(self):
        self.name=self.raw_json["name"]
        self.route_distinguisher=self.raw_json["route_distinguisher"]
        self.route_target_export=self.raw_json["route_target_export"]
        self.route_target_import=self.raw_json["route_target_import"]
        self.interfaces=self.raw_json["interfaces"]
        self.address_familys.append(AddressFamily(f"ipv4 vrf {self.name}",self.raw_json["members"],redistribute_connected=True))

    def export(self):
        to_send=f"vrf definition {self.name}\n"
        to_send+=f" rd {self.route_distinguisher}\n"
        to_send+=f" route-target export {self.route_target_export}\n"
        to_send+=f" route-target import {self.route_target_import}\n"
        to_send+=" address-family ipv4\n exit-address-family\n"
        return to_send

    def export_interface(self):
        return f" vrf forwarding {self.name}\n"


class MPLS:
    def __init__(self, MPLS_json):
        self.raw_json = MPLS_json
        self.interfaces = MPLS_json
    
    def export_interface(self):
        return f" mpls ip\n"
    
    def export_router(self):
        return ""


class BGP:
    def __init__(self, bgp_json):
        self.raw_json=bgp_json
        self.address_familys=[]


        self.load()

    def load(self):
        self.AS = self.raw_json['as-number']
        self.router_id = self.raw_json['router-id']
        if "IPV4" in self.raw_json.keys():
            self.address_familys.append(AddressFamily('ipv4',self.raw_json['IPV4']))
        if "VPNV4" in self.raw_json.keys():
            self.address_familys.append(AddressFamily('vpnv4',self.raw_json['VPNV4'],send_community=True))
    
    def add_address_family(self, address_family):
        self.address_familys.append(address_family)

    def export_router(self):
        to_send=f'router bgp {self.AS}\n'
        to_send+=f" bgp router-id {self.router_id}\n"
        to_send+=" bgp log-neighbor-changes\n"
        for address_family in self.address_familys:
            to_send+=address_family.export()
        return to_send

class OSPF:
    def __init__(self, OSPF_json):
        self.raw_json = OSPF_json

        self.load()
    
    def load(self):
        self.process_id = self.raw_json["process_id"]
        self.router_id = self.raw_json["router_id"]
        self.area = self.raw_json["area"]
        self.interfaces = self.raw_json["interfaces"]
    
    def export_router(self):
        return f"""router ospf {self.process_id}\n router-id {self.router_id}\n"""

    def export_interface(self):
        return f" ip ospf {self.process_id} area {self.area}\n"

class Interface:
    def __init__(self, interface_json):
        self.raw_json = interface_json
        self.protocols=[]
        self.vrfs=[]

        self.load()
    
    def load(self):
        if self.raw_json['id'][0] == 'g':
            self.type='GigabitEthernet'
            self.name='GigabitEthernet'+self.raw_json["id"][1]+"/0"
        elif self.raw_json['id'][0] == 'f':
            self.type='FastEthernet'
            self.name='FastEthernet0/0'
        else :
            self.type='Loopback'
            self.name='Loopback0'
        
        self.mask = self.raw_json['mask']
        self.ip = self.raw_json['address']
    

    def add_protocol(self, protocol):
        self.protocols.append(protocol)

    def add_vrf(self, vrf):
        self.vrfs.append(vrf)

    def export(self):
        to_send=f"interface {self.name}\n"
        for vrf in self.vrfs:
            to_send+=vrf.export_interface()
        
        to_send+=f" ip address {self.ip} {self.mask}\n"

        for protocol in self.protocols:
            to_send+=protocol.export_interface()
        
        to_send+=" no shutdown\n"

        return to_send


class Router:
    def __init__(self, router_name, router_json):
        self.name=router_name
        self.raw_json=router_json
        self.interfaces=[]
        self.protocols=[]
        self.vrfs=[]

        self.load()
    
    def load(self):
        for interface in self.raw_json['interfaces']:
            self.interfaces.append(Interface(interface))
        if "OSPF" in self.raw_json.get('protocols',{}).keys():
            ospf = OSPF(self.raw_json['protocols']["OSPF"])
            self.protocols.append(ospf)
            for i in self.raw_json['protocols']["OSPF"]["interfaces"]:
                self.interfaces[i].add_protocol(ospf)
        if "BGP" in self.raw_json.get('protocols',{}).keys():
            bgp = BGP(self.raw_json['protocols']["BGP"])
            self.protocols.append(bgp)
            for vrf_data in self.raw_json['protocols']["BGP"].get("VRFs",[]):
                vrf = VRF(vrf_data)
                self.vrfs.append(vrf)
                for interfaces in vrf.interfaces :
                    self.interfaces[interfaces].add_vrf(vrf)
                for address_family in vrf.address_familys:
                    bgp.add_address_family(address_family)
        if "MPLS" in self.raw_json.get('protocols',{}).keys():
            mpls = MPLS(self.raw_json['protocols']['MPLS'])
            self.protocols.append(mpls)
            for interface in mpls.interfaces :
                self.interfaces[interface].add_protocol(mpls)

    def export_interfaces(self):
        to_send=""
        for interface in self.interfaces:
            to_send+=interface.export()
        return to_send

    def export_vrf(self):
        to_send=''
        for vrf in self.vrfs:
            to_send+=vrf.export()
        return to_send

    def export_protocol(self):
        to_send=''
        for protocol in self.protocols:
            to_send+=protocol.export_router()
        return to_send

    def old_export(self):
        return f"""
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
hostname {self.name}
boot-start-marker
boot-end-marker
{self.export_vrf()}no aaa new-model
no ip icmp rate-limit unreachable
ip cef
no ip domain lookup
no ipv6 cef
multilink bundle-name authenticated
ip tcp synwait-time 5
{self.export_interfaces()}{self.export_protocol()}ip forward-protocol nd
no ip http server
no ip http secure-server
control-plane
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
end"""

    def export(self):
        return f"conf t\nhostname {self.name}\n{self.export_vrf()}{self.export_interfaces()}{self.export_protocol()}"


class PC:
    def __init__(self, pc_name, pc_json):
        self.name = pc_name
        self.raw_json = pc_json
        self.load()
    
    def load(self):
        self.address = self.raw_json["address"]
        self.mask = self.raw_json["mask"]
        self.gateway = self.raw_json["gateway"]

    def export(self):
        return f"ip {self.address} {self.mask} {self.gateway}"

class AutoConfig:
    def __init__(self):
        self.raw_json={}
        self.configs = []

    def load(self,json_file):
        self.__init__()
        f = open(json_file)
        self.raw_json = json.load(f)
        for config_name in self.raw_json.keys():
            if "PC" not in config_name:
                self.configs.append(Router(config_name,self.raw_json[config_name]))
            else :
                self.configs.append(PC(config_name,self.raw_json[config_name]))


    def export(self,export_path):
        for config in self.configs:
            f = open(export_path+config.name+".cfg",'w')
            f.write(config.export())
            f.close()

if __name__ == '__main__':
    config = AutoConfig()
    config.load(CONFIG_PATH)
    rmtree(EXPORT_PATH, ignore_errors=True)
    os.mkdir(EXPORT_PATH)
    config.export(EXPORT_PATH)
