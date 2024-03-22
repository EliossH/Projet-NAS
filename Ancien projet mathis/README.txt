Méthode pour éxécuter le code :
- Lancer GNS3
- Reproduire exactement la topologie indiquée dans l'image jointe du fichier .ZIP (avec les bons ports etc.)
- Lancer la simulation sur GNS3
- Lancez le script Projet.py et la topologie se saisiera automatiquement

Pour la configuration, voici tous les fichiers importants : 
- config/config.json : détient la configuration de tous les équipements du réseau (PC et routeur) avec les interfaces, les adresses et tous les critères nécessaires à la configuration BGP, OSPF etc.
- commands.py : fichier contenant toutes les fonctions permettant de configurer les interfaces, mettre en place les divers protocoles réseau etc.
- projet.py : script lançant automatiquement les instructions de configuration.
- Logs_Routeurs_Conf_Manuelle : on retrouve ici tous les logs des configurations de tous les routeurs de notre architecture. 

Dans le fichier .zip, se trouve aussi un projet Projets_Futurs, on y retrouve les possibles idées qu'on aurait aimé apporter à notre travail comme un comparateur.json. Le but était que le programme sauvegarde la configuration qu'il a réalisé dans un json. En cas de nouveau fichier de configuration, le programme allait comparer cette nouvelle configuration avec ce qu'il avait fait avant et rajouter/modifier ce qui a été changé entre les 2 scripts. Cela aurait ainsi évité de redémarrer tous les routeurs.