# Projet-NAS

Ce projet permet le deploiement automatique de réseau OSPF, BGP, MPLS et VPN dans GNS3.
Pour cela, il se base sur un fichiers d'intention au format json.
## Utilisation du projet
### Executable

Vous pouvez simplement lancer l'éxécutable `AutoConfigTelnet.exe` avec GNS3 d'ouvert sur votre projet et l'ensemble des routeurs lancés.

### Code Python

Vous pouvez éxécuter `python3 AutoConfigTelnet.py` dans les mêmes conditions pour le même résultat.

## Fichier d'intention

Le fichier `configReseau.json` est un fichier d'intentions associé au réseau suivant décrit par `PROJET NAS Diagramme.pdf`.

### Structure de base
Le fichier d'intention est composé d'une liste de router/PC identifiés par leur nom dans GNS3.

```json
{
    "PE1": {...},
    "P1": {...},
    "PC1": {...}
}
```

Pour chaque machine, on spécifie tout d'abord les interfaces et leur addressage IPv4:

```json
{
    "PE1": {
        "interfaces" :[{"id" : "loop 0",
                        "address": "1.1.1.1",
                        "mask" : "255.255.255.255"},
                        
                        {"id" : "g1/0",
                        "address": "192.168.1.1",
                        "mask" : "255.255.255.252"},
                    
                        {"id" : "g2/0",
                        "address": "192.168.21.1",
                        "mask" : "255.255.255.252"},
                    
                        {"id" : "g3/0",
                        "address": "192.168.11.1",
                        "mask" : "255.255.255.252"}]
    }
}
```
On peut ensuite spécifié une liste de protoole à configurer sur la machine :
```json
{
    "PE1" : {
        "interfaces": [...],
        "protocols":{
            "OSPF":{...},
            "BGP":{...},
            "MPLS":[...]
        }
    }
}
```

### OSPF

La configuration OSPF se fait en 4 éléments :
- process_id : L'identifiant du processus OSPF a créer
- router_id : Son identifiant au sein du réseau OSPF
- area : Le groupe de routeurs auquel il appartient
- interfaces : Une liste d'interfaces sur lesquelles échanger des paquets OSPF (C'est une liste d'indices faisant références aux indices des interfaces précédemment configurées) 

```json
{
    "PE1": {
        "interfaces" :[...],
        "protocols" : {
            "OSPF" :{
                "process_id": 1,
                "router_id": "1.1.1.1",
                "area": 0,
                "interfaces": [1, 0]
            }
        }
    }
}
```

### MPLS

La configuration MPLS est assez simple car les notions de VPN ont été configurés dans BGP, on retrouve ici uniquement les indices des interfaces sur lesquels activer MPLS.
```json
{
    "PE1": {
        "interfaces" :[...],
        "protocols" : {
            "MPLS" : [1, 2]
        }
    }
}
```

### BGP

La configuration BGP est un peu plus complexe :
```json
{
    "PE1": {
        "interfaces" :[...],

        "protocols" : {
            "BGP" :{
                "as-number":1,
                "router-id": "1.1.1.1",
                "VRFs": [
                    {
                        "name": "Client_A",
                        "route_distinguisher": "111:111",
                        "route_target_export": "111:1111",
                        "route_target_import": "111:1111",
                        "interfaces":[3],
                        "members":[{"neighbor-address":"192.168.11.2",
                                    "remote-as":11}]
                    },
                    {
                        "name": "Client_B",
                        "route_distinguisher": "222:222",
                        "route_target_export": "222:2222",
                        "route_target_import": "222:2222",
                        "interfaces":[2],
                        "members":[{"neighbor-address":"192.168.21.2",
                                    "remote-as":21}]
                    }
                ],
                "IPV4":[{"neighbor-address":"2.2.2.2",
                        "remote-as":1,
                        "update-source":"Loopback0"},
                        {"neighbor-address":"3.3.3.3",
                        "remote-as":1,
                        "update-source":"Loopback0"},
                        {"neighbor-address":"4.4.4.4",
                        "remote-as":1,
                        "update-source":"Loopback0"}],
                "VPNV4":[{"neighbor-address":"4.4.4.4"}]
            }
        }
    }
}
```
Tout d'abord, on retrouve les principaux éléments :
- as-number
- router-id

On a ensuite 2 types d'objets, des VRF et des Adress-Family.

Tout d'abord, les Address-Family "IPV4" et "VPNV4" sont des listes de voisins BGP associés à certains paramètres de configuration optionnelle.

Les VRF sont plus sofistiquées, on y retrouve :
- name : Le nom de la VRF
- route_distinguisher : Le RD associé à cette VRF
- route_target_export & route_target_import : Les RT en import et export associés à cette VRF, ils représentent le client
- interfaces : La liste des interfaces associées à cette VRF
- members : Une Address-Family BGP associée à cette VRF

# Auto-configurateur

L'autoconfigurateur est composé de 2 fichiers :
- `AutoConfig.py` qui va convertir le fichiers d'intention en un ensemble d'objet Python (Router, PC, Interfaces, BGP, OSPF, MPLS, VRF, AddressFamily...). Il en existe 2 types, les Hardwares (Router, PC, Interfaces) et les Protocoles (MPLS, BGP...). Les Hardwares contienent sous forme de liste, les interfaces et les protocoles associés. Si un protocole spécifiant une interface est défini sur un Routeur alors l'interface comme le routeur partageront le même objet Protocole. Les protocoles possédant des export différenciés pour les routeurs ou les interfaces. A la fin de l'éxécution, le programme va exporter l'ensemble des commandes à éxécuter dans GNS3.
- `AutoConfigTelnet.py`qui va récuperer l'ensemble des commandes précédemment générés, identifier les ports des machines virtuel, s'y connecter et transmettre en simultané l'ensemble des commandes.
