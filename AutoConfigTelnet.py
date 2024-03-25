import telnetlib3
import asyncio
import gns3fy

##créer la fonction qui retourne la correspondance routeur hostname - port associé
##créer la fonction qui charge les fichiers de confs dans un tableau


async def connect_to_router(host, port, config_commands):
    try:
        # Tentative de connexion au routeur via Telnet
        reader, writer = await telnetlib3.open_connection(host, port)
        print(f"Connexion réussie au routeur {host} sur le port {port}")

        # Envoyer des commandes de configuration
        for command in config_commands:
            writer.write(command+"\r\n")
            await writer.drain()
            await asyncio.sleep(1)  # Attendre une seconde entre chaque commande

        writer.close()
    except ConnectionRefusedError:
        print(f"Impossible de se connecter au routeur {host} sur le port {port}. Connexion refusée.")
    except Exception as e:
        print(f"Une erreur s'est produite lors de la connexion au routeur {host} sur le port {port}: {e}")

async def main():  
    host = "127.0.0.1"  
    ports = range(5000, 5016)  
    config_commands = [
    "version 15.2",
    "service timestamps debug datetime msec",
    "service timestamps log datetime msec",
    "hostname PE2",
    "boot-start-marker",
    "boot-end-marker",
    "no aaa new-model",
    "no ip icmp rate-limit unreachable",
    "ip cef",
    "no ip domain lookup",
    "no ipv6 cef",
    "multilink bundle-name authenticated",
    "ip tcp synwait-time 5",
    "interface Loopback0",
    " ip address 4.4.4.4 255.255.255.255",
    "interface GigabitEthernet1/0",
    " ip address 192.168.3.3 255.255.255.252",
    " negotiation auto",
    "interface GigabitEthernet2/0",
    " ip address 192.168.22.1 255.255.255.252",
    " negotiation auto",
    "interface GigabitEthernet3/0",
    " ip address 192.168.11.1 255.255.255.252",
    " negotiation auto",
    "ip forward-protocol nd",
    "no ip http server",
    "no ip http secure-server",
    "control-plane",
    "line con 0",
    " exec-timeout 0 0",
    " privilege level 15",
    " logging synchronous",
    " stopbits 1",
    "line aux 0",
    " exec-timeout 0 0",
    " privilege level 15",
    " logging synchronous",
    " stopbits 1",
    "line vty 0 4",
    " login",
    "end"
]

    tasks = [connect_to_router(host, 5000, config_commands)]# for port in ports]  # Création des tâches pour chaque connexion
    await asyncio.gather(*tasks)  # Attente que toutes les connexions soient terminées

# Exécuter la boucle d'événements asyncio
asyncio.run(main())
