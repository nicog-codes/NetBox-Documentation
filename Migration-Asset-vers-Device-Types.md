# Migration d'un inventaire Asset vers les Device Types NetBox

> **Statut :** méthodologie d'audit préparatoire, sans import automatique ni données d'inventaire d'une organisation.  
> **Cible du POC :** NetBox 4.6.x via API REST, sans modification de l'image NetBox.

## Objectif

Transformer un export d'outil de gestion des actifs en **catalogue normalisé de modèles matériels** à rapprocher des `Device Types` et `Module Types` NetBox. Ne pas confondre **nombre d'actifs** et **nombre de modèles**.

## Classification des entrées

| Nature de l'entrée source | Objet cible NetBox |
| --- | --- |
| Serveur, switch, firewall ou appliance physique | **Device Type** puis **Device** lors de l'inventaire unitaire |
| Baie de disques / storage shelf / châssis | **Device Type** (ou châssis parent suivant l'architecture) |
| Carte superviseur, linecard, carte réseau enfichable | **Module Type** et **Module Bay** si compatible avec le châssis |
| SFP/QSFP et autres transceivers | Choisir une méthode d'inventaire modulaire adaptée ; ne pas créer un switch par optique |
| Rack / armoire | Objet **Rack** |
| Patch panel, cassette, guide-câbles | Périphérique passif / modèle à qualifier |
| Feed A/B | Éléments de distribution électrique, **pas** un fabricant de PDU |
| Nom générique ou référence incomplète | **Revue manuelle** avant import |

## Rapprochement sécurisé

1. Extraire uniquement les désignations et types matériels nécessaires (sans IP, noms d'hôtes, numéros de série, localisations ou identifiants d'actifs).
2. Normaliser les préfixes constructeur et les variations de casse / ponctuation ; ne jamais fusionner aveuglément deux SKU.
3. Chercher d'abord une référence **existante dans NetBox** pour éviter les doublons.
4. Chercher ensuite une **correspondance unique** dans [netbox-community/devicetype-library](https://github.com/netbox-community/devicetype-library).
5. Ne pas interpréter une simple présence de dossier fabricant comme une preuve de disponibilité d'un modèle YAML précis.
6. Mettre de côté les résultats ambigus et les références sans YAML ; créer ces modèles manuellement à partir de spécifications fiables.
7. Contrôler les **interfaces réseau, ports d'alimentation, hauteurs, rôles parent/enfant et images avant/arrière** avant création.
8. Sauvegarder NetBox ; exécuter en mode simulation ; n'autoriser l'écriture qu'après revue.
9. Vérifier que les templates créés ne sont pas confondus avec des interfaces d'équipements physiques déjà présents.

## États d'un audit d'import

- `DEJA_DANS_NETBOX` : pas de création.
- `YAML_EXACT_A_IMPORTER` : correspondance unique ; vérifier la fiche technique avant application.
- `YAML_AMBIGU` : validation manuelle requise.
- `YAML_INTROUVABLE` : définition absente de la bibliothèque.
- `A_CREER_MANUELLEMENT` : constructeur absent ou matériel spécifique.
- `DOUBLON_NETBOX` : arbitrage nécessaire avant d'écrire.

## Retour d'expérience : prises électriques liées à un Power Port

Lors d'un lot supplémentaire de modèles issus de la bibliothèque communautaire, l'import des **Device Types**, images d'élévation et autres composants a réussi, mais certaines **Power Outlet Templates** ont été refusées avec :

```text
HTTP 400: Related objects must be referenced by numeric ID
or by dictionary of attributes. Received an unrecognized value: Input
```

D'autres valeurs de lien observées étaient `AC-Input 1`, `AC-Input 2` et `PS1`.

**Origine :** le champ YAML `power_port` donne un nom logique du port d'alimentation. Le champ API homonyme attend la référence de l'objet **Power Port Template** existant. L'importeur doit résoudre le nom en ID sur **le même Device Type**.

**Réparation sûre** :
1. Lire les YAML source et les `power-port-templates` / `power-outlet-templates` existants par API.
2. Identifier les prises manquantes par couple **Device Type ID + Outlet Name**.
3. Résoudre pour chaque prise son `power_port` par **Device Type ID + Power Port Name**.
4. Lancer une simulation en affichant les liens résolus, puis créer exclusivement les prises manquantes.
5. Vérifier le bilan final ; ne pas relancer tout l'import des modèles et ne pas écraser les composants existants.

Une exécution du POC a signalé **24 prises manquantes**, alors que les modèles, les images et les autres composants avaient été importés. **Ces 24 prises restent à vérifier après réparation** : le diagnostic ne prouve pas que le correctif a été exécuté.

Les ID numériques sont propres à chaque instance : **ne jamais les figer dans un YAML portable ni dans un script destiné à plusieurs installations**.

## Principes de confidentialité

**Ne pas publier l'export Asset, les quantités d'actifs, les modèles réellement déployés, les IP, les identifiants de matériels ni les rapports internes** dans le dépôt de documentation publique. Conserver le manifeste d'import, les comparaisons et les journaux détaillés sur un support privé et contrôlé.

Le script d'import et sa configuration API doivent rester distincts : seuls les algorithmes génériques peuvent être publics, jamais les jetons et fichiers d'inventaire.

## Suite du POC

- Valider la liste des modèles opérationnels par familles (serveur, stockage, réseau, châssis).
- Rechercher les YAML exacts et images avant/arrière de chaque référence.
- Réconcilier les modèles déjà présents et corriger les variantes de nommage.
- Importer par lots contrôlés avec traces et bilan d'erreurs.
- Produire ensuite un chantier séparé pour la migration des **Devices** (unités physiques, câblage, IP), qui nécessite une analyse des données individuelles et des autorisations appropriées.

*Cette page ne contient aucune donnée d'inventaire issue d'un environnement particulier.*
