import json
import os
from shutil import rmtree

CONFIG_PATH = 'configReseau.json'
EXPORT_PATH = 'exportConfig\\'

class Interface:
    def __init__(self, interface_json):
        print(interface_json)
        self.raw_json = interface_json

        #self.load()
    
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
        self.ip = self.raw_json['adresse']
    
    def export(self):
        pass

class Router:
    def __init__(self, router_name, router_json):
        print(router_name, router_json)
        self.name=router_name
        self.raw_json=router_json
        self.interfaces=[]

        #self.load()
    
    def load(self):
        for interface in self.raw_json['interfaces']:
            self.interfaces.append(Interface(interface))

    def export(self):
        return ''

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
