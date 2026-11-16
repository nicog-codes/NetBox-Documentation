# Listes d'impact réseau et électrique dans NetBox 4.6.9

> Guide public générique. Aucun équipement, câble, lien ou nom d'infrastructure interne n'est publié.

## Périmètre

- **Par switch** : ports, liaisons et équipements raccordés directement ou via panneaux de brassage ; pas un calcul automatique des services impactés.
- **Par PDU** : prises, alimentations des appareils, et existence éventuelle d'une autre PSU câblée.
- **Par Power Feed** : alimentation du PDU en amont, puis chemin explicite entre son Power Port et ses Power Outlets en aval.

## Pré-requis

Les Device Types ne suffisent pas : enregistrer les **Devices physiques**, leurs **Interfaces/Power Ports/Power Outlets**, les **Cables**, les **Power Panels/Power Feeds**, et les associations Power Outlet -> Power Port pour les PDU à plusieurs entrées.

## Navigation native

Sur un Device, ouvrir les Interfaces ou Power Outlets et utiliser l'action **Trace** sur la connexion câblée. Le tracé suit le câblage y compris les ports pass-through. Cela montre un chemin particulier, pas une liste complète d'impact par source.

## Méthode automatisable en lecture seule

### Switch

1. Identifier le Device switch.
2. Lister ses interfaces via /api/dcim/interfaces/?device_id=ID.
3. Lire les champs connected_endpoints ou appeler /api/dcim/interfaces/ID/trace/ pour chaque interface.
4. Rassembler et dédupliquer les appareils distants et signaler séparément les switches de transit et les liens non documentés.
5. Ne pas considérer comme interrompus tous les appareils derrière un switch distant ; LAG, MLAG, chemins alternatifs et services ne sont pas décrits par la seule topologie physique.

### PDU

1. Lister /api/dcim/power-outlets/?device_id=ID.
2. Pour chaque prise, identifier le port d'alimentation distant via connected_endpoints et le câblage.
3. Regrouper par serveur et PSU concernée ; chercher les autres PSU câblées.
4. Classer comme *perte d'une alimentation* ou *impact potentiellement total*, sans garantir une redondance réelle avant validation de l'indépendance A/B.

### Power Feed

1. Identifier le Power Feed en distinguant les éventuels noms identiques sur des Power Panels différents.
2. Utiliser /api/dcim/power-feeds/ID/trace/ pour retrouver le PDU raccordé.
3. Traverser la distribution *interne* du PDU : Power Port du PDU -> Power Outlets associées -> Power Ports des serveurs.
4. En cas de mapping manquant ou de sources redondantes indéterminées, produire un statut *données insuffisantes* plutôt qu'un faux impact.

## Export CSV recommandé

Colonnes : Source, Catégorie, Equipement distant, Interface/PSU, Port source/prise, Câble/chemin, Autre lien/PSU câblé, Statut d'impact potentiel, Incertitudes.

Un script externe dans le CT Docker existant peut effectuer ces trois analyses **sans écrire dans NetBox** ; l'exposition ultérieure dans l'UI NetBox peut être envisagée via un Custom Script. Les CSV réels doivent rester en espace privé.

## Références

- https://github.com/netbox-community/netbox/blob/v4.6.9/docs/models/dcim/cable.md
- https://github.com/netbox-community/netbox/blob/v4.6.9/docs/models/dcim/poweroutlet.md
- https://github.com/netbox-community/netbox/blob/v4.6.9/docs/models/dcim/powerfeed.md
- https://github.com/netbox-community/pynetbox/blob/main/docs/dcim.md
