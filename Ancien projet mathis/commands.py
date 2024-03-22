import time

def wait(tn, t):
    time.sleep(t)
    tn.read_until(b'#').decode('ascii')

def wait_PC(tn, t):
    time.sleep(t)
    tn.read_until(b'>').decode('ascii')

### GO ###
def go_conf(tn):
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')

def go_interface(tn, int):
    go_conf(tn)
    tn.write(b'interface gigabitEthernet' + str(int).encode() + b'/0\r\n')

def go_OSPF_process(tn, process_id):
    go_conf(tn)
    tn.write(b'router ospf ' + str(process_id).encode() + b'\r\n')

def go_BGP_process(tn, as_number):
    go_conf(tn)
    tn.write(b'router bgp ' + str(as_number).encode() + b'\r\n')

def go_address_family_vnpv4(tn, as_number):
    go_BGP_process(tn, as_number)
    tn.write(b'address-family vpnv4\r\n')

def go_address_family_ipv4(tn, as_number):
    go_BGP_process(tn, as_number)
    tn.write(b'address-family ipv4\r\n')

def go_vrf_def(tn, name):
    go_conf(tn)
    tn.write(b'vrf definition ' + str(name).encode() + b'\r\n')

def go_address_family_ipv4_vrf(tn, as_number, name):
    go_BGP_process(tn, as_number)
    tn.write(b'address-family ipv4 vrf ' + str(name).encode() + b'\r\n')

### CONFIG ###

# Interfaces
def create_loopbacks_address(tn, names, addresses, masks):
    for i in range(len(names)):
        create_loopback_address(tn, names[i], addresses[i], masks[i])

def create_loopback_address(tn, name, address, mask):
    go_conf(tn)
    tn.write(b'interface ' + str(name).encode() + b'\r\n')
    tn.write(b'ip address ' + str(address).encode() + b' ' + str(mask).encode() + b'\r\n')

def create_interfaces_address(tn, ids, addresses, masks):
    for i in range(len(ids)):
        create_interface_address(tn, ids[i], addresses[i], masks[i])

def create_interface_address(tn, int, address, mask):
    go_interface(tn, int)
    tn.write(b'ip address ' + str(address).encode() + b' ' + str(mask).encode() + b'\r\n')
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')

# OSPFv2
def config_OSPFv2(tn, process_id, router_id, area, ints, net):
    go_OSPF_process(tn, process_id)
    tn.write(b'mpls ldp autoconfig\r\n')
    tn.write(b'router-id ' + str(router_id).encode() + b'\r\n')
    tn.write(b'network ' + str(net).encode() + b' 0.0.0.0 area ' + str(area).encode() + b'\r\n')
    tn.write(b'end\r\n')
    for int in ints:
        config_OSPFv2_interface(tn, int, process_id, area)
        wait(tn, 1)
    
def config_OSPFv2_interface(tn, int, process_id, area):
    go_interface(tn, int)
    tn.write(b'ip ospf ' + str(process_id).encode() + b' area ' + str(area).encode() + b'\r\n')
    wait(tn, 0.5)
    tn.write(b'end\r\n')

# iBGP
def config_iBGP(tn, as_number, neighbors_loopback, neighbors_loopback_name):
    for i in range(len(neighbors_loopback)):
        config_iBGP_neighbor(tn, as_number, neighbors_loopback[i], neighbors_loopback_name[i])
        wait(tn, 1)

def config_iBGP_neighbor(tn, as_number, neighbors_loopback, neighbors_loopback_name):
    go_BGP_process(tn, as_number)
    tn.write(b'bgp log-neighbor-changes\r\n')
    tn.write(b'neighbor ' + str(neighbors_loopback).encode() + b' remote-as ' + str(as_number).encode() + b'\r\n')
    tn.write(b'neighbor ' + str(neighbors_loopback).encode() + b' update-source ' + str(neighbors_loopback_name).encode() + b'\r\n')
    go_address_family_vnpv4(tn, as_number)
    tn.write(b'neighbor ' + str(neighbors_loopback).encode() + b' activate\r\n')
    tn.write(b'neighbor ' + str(neighbors_loopback).encode() + b' send-community both\r\n')

# eBGP
def config_eBGP(tn, as_number, router_id, neighbors_address, neighbors_as_number, ip_networks_lan):
    go_BGP_process(tn, as_number)
    tn.write(b'bgp router-id ' + str(router_id).encode() + b'\r\n')
    for i in range(len(neighbors_address)):
        config_eBGP_neighbor(tn, as_number, neighbors_address[i], neighbors_as_number[i])
        wait(tn, 1)
        if ip_networks_lan != None:
            if ip_networks_lan[i] != None:
                for ip_network_lan in ip_networks_lan[i]:
                    config_eBGP_ip_networks_lan(tn, as_number, ip_network_lan)
                    wait(tn, 1)

def config_eBGP_neighbor(tn, as_number, neighbors_address, neighbors_as_number):
    go_BGP_process(tn, as_number)
    tn.write(b'neighbor ' + str(neighbors_address).encode() + b' remote-as ' + str(neighbors_as_number).encode() + b'\r\n')
    go_address_family_ipv4(tn, as_number)
    tn.write(b'neighbor ' + str(neighbors_address).encode() + b' activate\r\n')

def config_eBGP_ip_networks_lan(tn, as_number, ip_network_lan):
    go_address_family_ipv4(tn, as_number)
    tn.write(b'network ' + str(ip_network_lan).encode() + b'\r\n')

# VRF
def config_vrf(tn, name, as_number, rd, rte, rti, int, address, mask, neighbor_address, remote_as):
    go_vrf_def(tn, name)
    tn.write(b'rd ' + str(rd).encode() + b'\r\n')
    tn.write(b'route-target export ' + str(rte).encode() + b'\r\n')
    tn.write(b'route-target import ' + str(rti).encode() + b'\r\n')
    tn.write(b'address-family ipv4\r\n')
    go_address_family_ipv4_vrf(tn, as_number, name)
    tn.write(b'neighbor ' + str(neighbor_address).encode() + b' remote-as ' + str(remote_as).encode() + b'\r\n')
    tn.write(b'neighbor ' + str(neighbor_address).encode() + b' activate\r\n')
    config_vrf_forwarding(tn, name, int, address, mask)

def config_vrf_forwarding(tn, name, int, address, mask):
    go_interface(tn, int)
    tn.write(b'vrf forwarding ' + str(name).encode() + b'\r\n')
    tn.write(b'ip address ' + str(address).encode() + b' ' + str(mask).encode() + b'\r\n')
    wait(tn, 1)
    tn.write(b'no shutdown\r\n')
    
### PC ###
def config_pc_interface(tn, ip, mask, gw):
    tn.write(b'ip ' + str(ip).encode() + b' ' + str(mask).encode() + b' ' + str(gw).encode() + b'\r\n')
    wait_PC(tn, 1)
    tn.write(b'save\r\n')

### SAVE ###
def save_config(tn):
    tn.write(b'end\r\n')
    tn.write(b'write mem\r\n')
    tn.write(b'\r\n')