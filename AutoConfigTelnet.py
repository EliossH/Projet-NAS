import telnetlib3
import asyncio
from gns3fy import Gns3Connector, Project, Node, Link
import os
import AutoConfig

##créer la fonction qui retourne la correspondance routeur hostname - port associé
##créer la fonction qui charge les fichiers de confs dans un tableau


async def connect_to_router(host, port, config_commands):
    try:
        # Tentative de connexion au routeur via Telnet
        reader,writer = await telnetlib3.open_connection(host, port)
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


def get_router_ports():
    SERVER_URL = "http://localhost:3080"
    # Define the connector object, by default its port is 3080
    server = Gns3Connector(url=SERVER_URL)
    telnet_ports = {}

    try:
        # Now obtain a project from the server
        lab = Project(name="projet_NAS_2024", connector=server)
        lab.get()

        # Iterate through each node in the project
        for node in lab.nodes:
            telnet_ports[node.name]=node.console
            #print("Node Name:", node.name)
            #print("Node Port:", node.console)
            
            # Check if the node is a router
         
    except Exception as e:
        print("Error retrieving project information:", e)

    return telnet_ports


def lister_fichiers(repertoire):
    # Initialiser une liste pour stocker les noms des fichiers
    fichiers = []
    
    AutoConfig.execute_AutoConfig()

    # Parcourir tous les fichiers dans le répertoire spécifié
    for nom_fichier in os.listdir(repertoire):
        # Vérifier si le chemin est un fichier
        chemin_absolu = os.path.join(repertoire, nom_fichier)
        if os.path.isfile(chemin_absolu):
            # Ajouter le nom du fichier à la liste
            fichiers.append(nom_fichier.split(".")[0])
    
    return fichiers



async def main():  
    host = "127.0.0.1"
    liste_routeurs=lister_fichiers("./exportConfig")
    liste_ports=get_router_ports()

    tasks=[]
    tab_debut=["\r\n","\r\n","\r\n"]
    config_commands =""
    for i in range (len(liste_routeurs)):
        
        try:
            # Ouvrir le fichier en mode lecture
            with open("./exportConfig/"+liste_routeurs[i]+".cfg", 'r') as fichier:
                # Lire tout le contenu du fichier
                config_commands = fichier.read().split("\n")
                
        except FileNotFoundError:
            print("Le fichier spécifié est introuvable.")
        except Exception as e:
            print("Une erreur s'est produite lors du chargement du fichier:", e)
        
        tasks.append(connect_to_router(host, liste_ports[liste_routeurs[i]], tab_debut+config_commands))
    await asyncio.gather(*tasks)
 
    


# for port in ports]  # Création des tâches pour chaque connexion
      # Attente que toutes les connexions soient terminées
    
# Exécuter la boucle d'événements asyncio
asyncio.run(main())
#print(get_router_ports()["PE1"])
#print(lister_fichiers("./exportConfig"))