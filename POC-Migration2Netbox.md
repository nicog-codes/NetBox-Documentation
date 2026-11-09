# POC Migration2Netbox — Import des modèles HPE, Cisco et Nutanix

> **Périmètre :** NetBox 4.6.9, import des *Device Types* et des images avant/arrière via l'API REST.  
> **Objectif :** enrichir l'inventaire matériel sans installer de plugin dans NetBox et sans modifier le conteneur applicatif.  
> **Statut :** import HPE/Cisco réalisé ; extension Nutanix effectuée avec définitions provisoires, à valider matériellement.

## 1. Contexte

Le POC vise à accélérer la constitution d'un inventaire NetBox couvrant les serveurs, switches, châssis et leurs composants (interfaces, ports électriques, baies de modules, etc.). Les modèles et images sont récupérés depuis la bibliothèque communautaire lorsque disponibles.

Architecture générale :

```text
GitHub Device Type Library
          |
          v
Conteneur temporaire d'import (Docker)
          |
          | API REST HTTPS + token dédié
          v
    NetBox 4.6.9
     |        |
 Device Types  Élévations de baies
     |
 Ports / composants / images
```

Le collecteur/importeur est **indépendant de NetBox** : il est lancé à la demande. Les modifications portent sur les **données de l'inventaire** via API, et non sur le code ou l'image de NetBox. Une sauvegarde de la base et des fichiers média reste nécessaire avant un import massif.

## 2. Source des modèles et des images

Bibliothèque utilisée : [netbox-community/devicetype-library](https://github.com/netbox-community/devicetype-library).

- `device-types/HPE` et `device-types/Cisco` : définitions YAML.
- `elevation-images/HPE` et `elevation-images/Cisco` : images d'élévation avant/arrière disponibles.
- Le script d'import filtre les constructeurs souhaités et ne réimporte pas les modèles identiques déjà présents.

L'identification des doublons repose sur le constructeur et le modèle. Les images existantes ne doivent pas être écrasées sans décision explicite.

## 3. Procédure d'import HPE / Cisco

### 3.1 Préparation

Le POC utilise un importeur Python conteneurisé interrogeant l'API NetBox. Le code précis de l'importeur dépend du déploiement local et n'est pas fourni dans cet article.

Créer un jeton API **dédié**, limité aux autorisations nécessaires à l'ajout de constructeurs, modèles, composants et images. Conserver les secrets dans un fichier d'environnement local exclu du contrôle de version.

Exemple de configuration (valeurs fictives) :

```dotenv
NETBOX_URL=https://netbox.example.org
NETBOX_TOKEN=<TOKEN_NON_PUBLIE>
```

### 3.2 Simulation puis exécution

Commandes de l'importeur utilisé dans ce POC :

```bash
# Dans le répertoire de l'importeur Docker
# Simulation limitée à cinq modèles
docker compose run --rm netbox-library-import --vendors HPE,Cisco --limit 5

# Simulation complète : pas d'écriture dans NetBox
docker compose run --rm netbox-library-import --vendors HPE,Cisco

# Import réel, après vérification du bilan et sauvegarde
docker compose run --rm netbox-library-import --vendors HPE,Cisco --apply
```

Ces commandes concernent **cet importeur particulier** ; elles ne font pas partie de la CLI native de NetBox.

### 3.3 Résultats constatés

| Indicateur | Résultat |
| --- | ---: |
| Modèles créés | **1 608** |
| Modèles existants conservés | **2** |
| Images importées | **1 047** |
| Composants créés lors du premier passage | **44 344** |
| Erreurs de modèles | **0** |
| Erreurs d'images | **0** |
| Erreurs de composants | **10** |
| YAML rejetés | **0** |

Les dix erreurs restantes étaient concentrées sur les modèles **HPE ProCurve 600** et **ProCurve 630** et concernaient des *power outlet templates* ; le reste de l'import a été effectué correctement.

## 4. Correction des relations Power Outlet / Power Port

Lors de la création de plusieurs prises (RPS/EPS) sur les modèles ProCurve, l'API renvoyait :

```text
HTTP 400: power_port: Related objects must be referenced by numeric ID
or by dictionary of attributes. Received an unrecognized value: PS1
```

### Cause

La source utilisait le nom logique `PS1`. L'API de NetBox exige pour la relation `power_port` l'identifiant numérique d'un **Power Port Template** existant (ou une représentation imbriquée valide), et non une chaîne de caractères libre.

### Correctif

Le correctif recherche d'abord le modèle et son port `PS1` dans NetBox, puis utilise l'identifiant renvoyé par l'API :

```python
# Illustration de la résolution, non exécutable seule
ps1_id = next(
    port["id"] for port in power_port_templates
    if port["device_type"]["id"] == device_type_id
    and port["name"] == "PS1"
)

payload = {
    "device_type": device_type_id,
    "name": "RPS1",
    "power_port": ps1_id,
}
```

Un script de correction a permis de repérer **10 prises manquantes, sans erreur en simulation** :

- ProCurve 600 : `RPS1` à `RPS6`, `EPS1` et `EPS2`.
- ProCurve 630 : `RPS` et `EPS`.

La simulation vérifiée donne **10 composants à corriger, 0 erreur**. Il faut consulter l'instance pour confirmer le bilan exact après application du correctif. Le script est conçu pour éviter de recréer une prise déjà présente.

## 5. Extension Nutanix : YAML spécifiques au POC

La référence recherchée en premier lieu était **Nutanix NX-8170A-G10**. Aucun répertoire Nutanix n'était disponible dans la bibliothèque communautaire interrogée lors de l'étude. L'utilisation d'un châssis Supermicro ressemblant n'a pas été considérée comme une preuve d'équivalence OEM.

Une bibliothèque complémentaire de **33 fichiers YAML** (générations G7 à G10) a été générée sur l'environnement d'import. Les objets utilisent les clés NetBox pertinentes :

```yaml
# Exemple minimal illustratif : pas une fiche constructeur certifiée.
manufacturer: Nutanix
model: NX-8170A-G10
slug: nutanix-nx-8170a-g10
part_number: NX-8170A-G10
u_height: 1
is_full_depth: true
power-ports:
  - name: PSU1
    type: other
  - name: PSU2
    type: other
```

**Attention :** les hauteurs, l'architecture châssis/nœuds, les types d'alimentation, les ports et les options réseau devront être **vérifiés sur le matériel et dans la documentation constructeur**. Ces YAML restent des modèles provisoires destinés au POC, pas une bibliothèque matérielle officielle.

### Résultat de la simulation

```text
33 YAML générés
models_to_create     : 33
models_existing      : 0
templates_to_create  : 73
errors               : 0
```

L'import effectif a été indiqué comme effectué ; son bilan chiffré complet n'a pas été fourni dans les journaux utilisés pour cet article. Il doit être vérifié avant de conclure à la création effective des 33 modèles et 73 composants.

**Images Nutanix :** aucune image avant/arrière n'a été importée dans ce lot. La récupération ou la création de vues exactes reste un travail à part.

## 6. HTTPS et bonnes pratiques de sécurité

Le POC a rencontré un certificat HTTPS autosigné avec un nom non adapté à l'URL utilisée. Le diagnostic a confirmé l'accès à l'API HTTPS, puis un contournement temporaire a été appliqué côté importeur.

Pour une installation durable, il est préférable de :

1. Utiliser un certificat HTTPS valide pour le **nom DNS réellement utilisé** (extension SAN correcte).
2. Ajouter l'autorité de certification interne au magasin de confiance de l'importeur.
3. Maintenir la **vérification TLS activée**.
4. Utiliser un compte d'API dédié avec les droits minimaux et faire tourner les tokens régulièrement.
5. Ne jamais inscrire de token, mot de passe, adresse interne ou empreinte d'infrastructure dans un dépôt public.

La simple désactivation de la validation TLS (`verify=False`) n'est **pas** une configuration recommandée.

## 7. Vérifications et perspectives

Avant un import : sauvegarde PostgreSQL et médias, simulation complète, inspection des différences et contrôle des permissions. Après import : vérifier les *Device Types*, la présence des ports et images, puis les vues de baies.

Travaux envisagés : ajout de références Nutanix validées constructeur, représentation détaillée des châssis multi-nœuds, liaison avec les équipements physiques, collecte SNMP des PDU pour la consommation (via un outil de télémétrie dédié), et authentification LDAP/Active Directory selon le besoin.

## Références

- [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library)
- [Documentation NetBox](https://netboxlabs.com/docs/netbox/)
- [Plateformes matérielles Nutanix](https://www.nutanix.com/products/hardware-platforms/specsheet)

---

*Article public et anonymisé. Il décrit des résultats d'un POC ; il ne constitue pas une recette générique garantie pour toutes les versions de NetBox.*
