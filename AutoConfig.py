import json
import os
from shutil import rmtree

CONFIG_PATH = 'configReseau.json'
EXPORT_PATH = 'exportConfig\\'

class AddressFamily:
    def __init__(self, name, address_family_json):
        self.name = name
        self.members = address_family_json
    
    def export(self):
        to_send=f" address-family {self.name}\n"
        for member in self.members:
            to_send+=f"  neighbor {member['neighbor-address']} remote-as {member['remote-as']}\n"
            if member.get("update-source","")!="":
                to_send+=f"  neighbor {member['neighbor-address']} update-source {member['update-source']}\n"
            to_send+=f"  neighbor {member['neighbor-address']} activate\n"
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
        self.address_familys.append(AddressFamily(f"vrf {self.name}",self.raw_json["members"]))

    def export(self):
        to_send=f"vrf definition {self.name}\n"
        to_send+=f" rd {self.route_distinguisher}\n"
        to_send+=f" route-target export {self.route_target_export}\n"
        to_send+=f" route-target import {self.route_target_import}\n"
        to_send+=" address-family ipv4\n exit-address-family\n"
        return to_send

    def export_interface(self):
        return f" vrf forwarding {self.name}\n"

class BGP:
    def __init__(self, bgp_json):
        self.raw_json=bgp_json
        self.address_familys=[]


        self.load()

    def load(self):
        self.AS = self.raw_json['as-number']
        self.router_id = self.raw_json['router-id']
        self.address_familys.append(AddressFamily('ipv4',self.raw_json['IPV4']))
    
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
        return f"""router ospf {self.process_id}
 router-id {self.router_id}\n"""

    def export_interface(self):
        return f" ip ospf {self.process_id} area {self.area}\n"

class Interface:
    def __init__(self, interface_json):
        print(interface_json)
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
        print(self.name, self.ip, self.mask)
    

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
        
        if self.type != 'Loopback':
            to_send+=" negotiation auto\n"

        return to_send


class Router:
    def __init__(self, router_name, router_json):
        print(router_name, router_json)
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
            for vrf_data in self.raw_json['protocols']["BGP"]["VRFs"]:
                vrf = VRF(vrf_data)
                self.vrfs.append(vrf)
                for interfaces in vrf.interfaces :
                    self.interfaces[interfaces].add_vrf(vrf)
                for address_family in vrf.address_familys:
                    bgp.add_address_family(address_family)


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

    def export(self):
        return f"""version 15.2
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

class AutoConfig:
    def __init__(self):
        self.raw_json={}
        self.routers = []

    def load(self,json_file):
        self.__init__()
        f = open(json_file)
        self.raw_json = json.load(f)
        print(self.raw_json)
        for router_name in self.raw_json.keys():
            self.routers.append(Router(router_name,self.raw_json[router_name]))


    def export(self,export_path):
        for router in self.routers:
            f = open(export_path+router.name+".cfg",'w')
            f.write(router.export())
            f.close()

if __name__ == '__main__':
    config = AutoConfig()
    config.load(CONFIG_PATH)
    rmtree(EXPORT_PATH, ignore_errors=True)
    os.mkdir(EXPORT_PATH)
    config.export(EXPORT_PATH)
