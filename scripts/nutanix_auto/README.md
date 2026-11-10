# Nutanix — automatisation des images NetBox

L'outil Docker télécharge les pochoirs Nutanix G7, G8, G9, G10 depuis VisioCafe, tente l'extraction et la conversion en PNG de chaque vue identifiable, compare les noms de modèles aux Device Types Nutanix existants dans l'API NetBox, puis lance une simulation. Il n'y a aucun changement dans NetBox sans l'argument --apply.

## Sur le CT 103

Le fichier /opt/netbox-import/netbox-library-import/.env doit déjà contenir NETBOX_URL et NETBOX_TOKEN.

Première exécution :

    curl -fsSL https://raw.githubusercontent.com/nicog-codes/NetBox-Documentation/main/scripts/nutanix_auto/bootstrap.sh -o /tmp/nutanix-bootstrap.sh
    cat /tmp/nutanix-bootstrap.sh
    bash /tmp/nutanix-bootstrap.sh

Les fichiers sont stockés sous /opt/netbox-import/nutanix-auto/data :

- controle.html : galerie des vues trouvées, à vérifier visuellement ;
- manifest.json : fichier des correspondances et avertissements ;
- png/ : images sélectionnées automatiquement ;
- archives/ : sources ZIP en cache (les téléchargements ne sont pas refaits inutilement) ;
- racklibrary/ : entrée facultative des exports RackLibrary.

**Après avoir vérifié les images dans controle.html**, application :

    bash /tmp/nutanix-bootstrap.sh --apply

Le script d'import ne remplace pas les images existantes et cible uniquement les modèles du fabricant Nutanix. Il ne change pas les interfaces Ethernet, ni les Devices existants.

## Limite technique des pochoirs Visio

Certaines vues utilisent EMF/WMF. Le convertisseur simplifié vss2xhtml peut ne pas les rendre correctement. L'outil les refuse pour éviter d'importer des rendus vides/incomplets.

**Repli pour ces fichiers :** ouvrir https://racklibrary.rtm516.co.uk/ ; importer les ZIP disponibles dans data/archives ; exporter en une seule archive ZIP avec les images PNG et le manifest.json. Copier cette archive dans data/racklibrary/ et relancer le bootstrap en simulation. Les rendus RackLibrary sont prioritaires sur les rendus du convertisseur simplifié, et les variantes ambiguës sont écartées.

Un contrôle visuel reste nécessaire, notamment pour les façades, les options de cartes et les faces arrière. Ne pas utiliser une image d'un autre SKU ou une vue isométrique dans NetBox.

## Sécurité et copyright

Le bootstrap applique NETBOX_TLS_VERIFY=false uniquement pour le POC avec certificat autosigné : ce contournement doit être supprimé après installation d'un certificat NetBox valide. Les fichiers Visio et leurs images converties sont stockés localement, pas dans le Git public. La collection Nutanix VisioCafe est créditée Nutanix / VSD Grafx ; les droits de réutilisation ou redistribution doivent être respectés.

Sources : https://www.visiocafe.com/nutanix.htm ; https://github.com/rtm516/RackLibrary ; https://github.com/LibreOffice/libvisio
