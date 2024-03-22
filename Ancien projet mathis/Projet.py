from gns3fy import Gns3Connector, Project
import telnetlib
import json
import commands

with open('config/config.json', 'r') as configFile:
    data = configFile.read()

configs = json.loads(data)

NAME = ""
PROJECT_ID = ""

server = Gns3Connector("http://localhost:3080")

for data in server.projects_summary(is_print=False):
    if (data[4] == "opened"):
        NAME = data[0]
        PROJECT_ID = data[1]

lab = Project(name=NAME, connector=server)

lab.get()

Project(project_id=PROJECT_ID, name=NAME, status='opened')

lab.open()

for node in lab.nodes:
    tn = telnetlib.Telnet("localhost", node.console)
    
    if "PC" in node.name:
        data = configs[node.name]
        commands.config_pc_interface(tn, data["address"], data["mask"], data["gateway"])
        print ("On a configuré " + node.name)
        continue
    for config in configs[node.name]:
        for key in config:
            if isinstance(config[key], dict):
                
                tn.write(b'\r\n')
                tn.write(b'end\r\n')
                commands.wait(tn, 3)

                for sub_key in config[key]:
                    if isinstance(config[key], dict):
                        data = config[key][sub_key]
                        match sub_key:
                            case "gigabitEthernet":
                                commands.create_interfaces_address(tn, data["ids"], data["addresses"], data["masks"])
                            case "loopback":
                                commands.create_loopbacks_address(tn, data["names"], data["addresses"], data["masks"])
                            case "OSPFv2":
                                commands.config_OSPFv2(tn, data["process_id"], data["router_id"], data["area"], data["interfaces"], configs[node.name][0]["interfaces"]["loopback"]["addresses"][0])
                            case "iBGP":
                                commands.config_iBGP(tn, data["as_number"], data["neighbors_loopback"], data["neighbors_loopback_name"])
                            case "eBGP":
                                commands.config_eBGP(tn, data["as_number"], data["router_id"], data["neighbors_address"], data["neighbors_as_number"], data["ip_networks_lan"])
                                if "VRFs" in data.keys():
                                    for VRF in data["VRFs"]:
                                        commands.config_vrf(tn, VRF["name"], VRF["as_number"], VRF["route_distinguisher"], VRF["route_taget_export"], VRF["route_target_import"], VRF["interface"], VRF["address"], VRF["mask"], VRF["neighbor_address"], VRF["remote_as"])
                            case _:
                                print("error")
                tn.write(b'end\r\n')
            else:
                print("error")
    
    tn.write(b'end\r\n')
    tn.write(b'write mem\r\n')
    tn.read_until(b'[confirm]').decode('ascii')
    tn.write(b'\r\n')

    tn.close()

    print ("On a configuré " + node.name)

configFile.close()