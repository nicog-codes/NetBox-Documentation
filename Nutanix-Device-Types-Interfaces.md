# Nutanix dans NetBox 4.6.9 — modèles YAML, interfaces et validation matérielle

> **Statut :** documentation du POC ; inventaire réseau **partiellement modélisé**.  
> **Dernière mise à jour :** novembre 2026.  
> **Confidentialité :** les adresses internes, comptes et chemins propres à un environnement privé ne sont pas publiés.

## Objectif et périmètre

Compléter dans NetBox les modèles de serveurs **Nutanix NX** avec leurs connectiques réseau et électriques, sans modifier l'installation NetBox. Les modèles ont été créés initialement avec des ports d'alimentation et, pour certains châssis, des emplacements de nœuds ; les **interfaces réseau étaient absentes**.

Ce document distingue explicitement :

- **Observé dans les journaux du POC :** les opérations et simulations réellement exécutées ;
- **Proposé / à vérifier :** les interfaces candidates, variables selon les cartes réseau et le SKU exact ;
- **En attente :** l'inventaire matériel (AIOM / OCP / PCIe) à confirmer avant généralisation.

Le modèle de travail principal est **NX-8170A-G10**. Une déclinaison **NX-8170A-G10-A9355-CM** a été identifiée ; elle doit être traitée comme une référence de configuration/part number à rapprocher de la fiche constructeur, pas automatiquement comme une définition de ports distincte. La présence des interfaces natives/optionnelles n'est **pas démontrée** par la seule référence de processeur.

## 1. Bibliothèque YAML Nutanix générée

La recherche dans [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library) n'avait pas trouvé de répertoire `device-types/Nutanix` ni de répertoire `elevation-images/Nutanix` ; la bibliothèque Supermicro présente des modèles voisins, **pas de correspondance OEM formellement prouvée** pour le NX-8170A-G10.

Un générateur local a donc produit **33 YAML Nutanix G7/G8/G9/G10**. Ils sont destinés au POC, pas à une publication comme spécifications officielles.

### Simulation initiale

```text
33 YAML generes
BILAN: {
  'models_to_create': 33,
  'models_created': 0,
  'models_existing': 0,
  'templates_to_create': 73,
  'templates_created': 0,
  'errors': 0
}
```

L'import réel des modèles a été indiqué comme effectué, mais son **bilan d'exécution détaillé n'a pas été conservé dans les éléments disponibles pour cette documentation**. Il faut interroger NetBox pour confirmer la quantité exacte d'objets effectivement présents.

### Limites de ces fichiers

- Les champs `manufacturer`, `model`, `slug`, `part_number`, `u_height`, `is_full_depth` ont été définis.
- Les modèles simples ont reçu **deux Power Port Templates génériques** (`PSU1`, `PSU2`) ; cela représente un schéma de travail, pas une preuve de PSU réelle pour chacun.
- Certains modèles multi-nœuds ont été configurés avec des **Device Bays** sur un modèle parent. Leurs interfaces réseau doivent être ajoutées **au modèle du nœud concerné**, pas arbitrairement au châssis.
- Les variantes de cartes AIOM/OCP/PCIe ne sont pas décrites de manière exhaustive.
- **Aucune image avant/arrière** Nutanix n'a été intégrée lors de cette opération.
- La hauteur, la structure physique, le PSU et les types de ports doivent être vérifiés pour chaque référence.

## 2. Première campagne de modèles réseau (simulation)

Un script local `fix_nutanix_network.py` a été préparé. Il utilise l'API `dcim/device-types/` et `dcim/interface-templates/` afin d'ajouter les interfaces absentes sans recréer les modèles.

Hypothèses de ports **proposées** pour un premier lot, **non vérifiées sur les équipements individuels** :

| Modèle | Interfaces candidates | Statut |
| --- | --- | --- |
| `NX-3155G-G8` | IPMI 1 GbE ; 2 × 10GBASE-T ; 2 × SFP+ | Proposition ; vérifier contrôleurs et ports |
| `NX-8170-G9` | IPMI 1 GbE ; 2 × 10GBASE-T (AIOM) | Proposition ; vérifier la variante AIOM |
| `NX-8150-G10` | IPMI 1 GbE ; 2 × 10GBASE-T (AIOM) | Proposition ; vérifier la variante AIOM |
| `NX-8170-G10` | IPMI 1 GbE ; 2 × 10GBASE-T (AIOM) | Proposition ; vérifier la variante AIOM |

Journal de simulation **constaté** :

```text
AJOUT: NX-3155G-G8 IPMI 1000base-t
AJOUT: NX-3155G-G8 Onboard 10GBase-T 1 10gbase-t
AJOUT: NX-3155G-G8 Onboard 10GBase-T 2 10gbase-t
AJOUT: NX-3155G-G8 Onboard SFP+ 1 10gbase-x-sfpp
AJOUT: NX-3155G-G8 Onboard SFP+ 2 10gbase-x-sfpp
AJOUT: NX-8170-G9 IPMI 1000base-t
AJOUT: NX-8170-G9 AIOM 10GBase-T 1 10gbase-t
AJOUT: NX-8170-G9 AIOM 10GBase-T 2 10gbase-t
AJOUT: NX-8150-G10 IPMI 1000base-t
AJOUT: NX-8150-G10 AIOM 10GBase-T 1 10gbase-t
AJOUT: NX-8150-G10 AIOM 10GBase-T 2 10gbase-t
AJOUT: NX-8170-G10 IPMI 1000base-t
AJOUT: NX-8170-G10 AIOM 10GBase-T 1 10gbase-t
AJOUT: NX-8170-G10 AIOM 10GBase-T 2 10gbase-t
BILAN: 14 à créer, 0 créés, 0 erreurs
```

**Interprétation :** le mode simulation a détecté **14 templates manquants** et aucune erreur de préparation ; **0 interface n'a été créée par ce test**. Aucune sortie d'exécution `--apply` correspondante n'a été transmise. Ne pas présenter ces quatorze ports comme déjà installés ou comme matériels certifiés.

### Commande de simulation

Lancée depuis l'environnement Docker d'importation, dans lequel `fix_nutanix_network.py` est conservé localement :

```bash
docker compose run --rm \
  -v "$PWD/fix_nutanix_network.py:/app/fix_nutanix_network.py:ro" \
  --entrypoint python \
  netbox-library-import /app/fix_nutanix_network.py
```

Ce script n'est **pas** un composant standard de NetBox ; il fait partie du POC local. Avant tout `--apply`, comparer les ports proposés aux données matérielles et sauvegarder NetBox.

## 3. Piège de nommage : NX-8150-G10 vs NX-8150G-G10

Un écran NetBox présentait **`NX-8150G-G10`** avec uniquement l'onglet **Power Ports (2)** et aucun onglet Interfaces.

Le script initial ciblait **`NX-8150-G10`** (tiret supplémentaire, sans « G » après 8150). Les deux libellés ne sont **pas identiques** et ne doivent pas être fusionnés automatiquement.

Un ajout au dictionnaire de configuration du script a été proposé :

```python
# À vérifier selon l'équipement : proposition, pas validation OEM.
"NX-8150G-G10": [ipmi, *aiom],
```

Avant de modifier des objets :
1. Identifier le **SKU constructeur** et sa graphie exacte.
2. Rechercher d'éventuels doublons dans NetBox.
3. Décider si `NX-8150-G10` et `NX-8150G-G10` sont deux variantes réelles ou une erreur de saisie.
4. Corriger l'inventaire et seulement ensuite appliquer les interfaces validées.

## 4. Référence précise étudiée : NX-8170A-G10-A9355-CM

Une référence détaillée a été communiquée pour le matériel étudié :

```text
Nutanix NX-8170A-G10-A9355-CM
```

**Ce qui est établi dans l'étude :** il s'agit de la référence communiquée ; la famille de modèle NetBox pertinente est `NX-8170A-G10`.

**Ce qui ne l'est pas encore :** la liste des contrôleurs, ports physiques natifs, cartes AIOM/OCP, adaptateurs PCIe, vitesse et type des connecteurs réseau. Une référence proche comportant `A9355` ne suffit pas à confirmer les ports.

Préconisation de modélisation NetBox, à valider :

| Champ | Proposition |
| --- | --- |
| Manufacturer | `Nutanix` |
| Device Type | `NX-8170A-G10` |
| Part Number / variant | `NX-8170A-G10-A9355-CM`, après vérification de la nomenclature |
| Management | Créer l'interface BMC/IPMI uniquement après confirmation du port physique |
| Ports réseau | Déclarer les interfaces effectivement présentes ; distinguer ports fixes et cartes optionnelles |
| Images | Ajouter des vues avant/arrière exactes et autorisées à être réutilisées |

**Point en attente : retour de l'ingénieur** avec l'inventaire réseau réel. Il n'est pas prévu de déduire arbitrairement des ports sur les 33 modèles à partir de cette seule référence.

## 5. Collecte matérielle pour valider les ports

Sur un hôte Nutanix AHV, un ingénieur disposant des accès autorisés peut relever, en lecture seule :

```bash
# Contrôleurs Ethernet détectés par PCI
lspci -nn | grep -Ei 'Ethernet|Network'

# Interfaces vues par Linux
ip -br link

# Exemple : pilote / bus associé à une interface identifiée
ethtool -i <interface>
```

Selon le BIOS/BMC et les outils disponibles, compléter par l'inventaire de la carte AIOM/OCP/PCIe, la documentation OEM, les labels physiques arrière et/ou des photos. `lspci` montre les fonctions PCI ; **il ne prouve pas à lui seul le nombre exact de prises RJ45/SFP physiques**.

Pour chaque port, conserver :

| Donnée attendue | Exemple de valeur à confirmer |
| --- | --- |
| Modèle matériel et SKU | Référence constructeur |
| Carte / slot | Onboard, AIOM, OCP ou PCIe |
| Nom physique du port | Port 1 / Port 2 / BMC |
| Connecteur et vitesse | RJ45 1G/10G, SFP+, SFP28, QSFP… |
| Interface AHV | Nom Linux et adresse MAC |
| Statut | Présent / optionnel / non équipé |
| Source | Sortie CLI, BMC, photo, fiche constructeur |

**Respecter les règles de confidentialité :** ne pas publier dans ce dépôt public les adresses MAC internes, IP de management, noms d'hôtes, captures BMC ou numéros de série de l'infrastructure étudiée.

### Premier retour terrain : commande exécutée sur une CVM, et non sur l'hôte AHV

Un premier relevé `lspci -nn | grep -Ei 'Ethernet|Network'` a été fourni depuis une **Controller VM (CVM)**. La sortie indiquait **quatre contrôleurs réseau VirtIO** (`Red Hat, Inc. Virtio network device [1af4:1000]`, fonctions PCI `00:04.0` à `00:07.0`).

**Conclusion :** ce résultat représente les **interfaces réseau virtuelles de la CVM**, et non les adaptateurs ni ports physiques du nœud Nutanix. **Aucune interface physique ne doit être créée dans le Device Type à partir de ces quatre entrées VirtIO.**

**Action demandée :** relever les contrôleurs depuis la session SSH de l'**hôte hyperviseur AHV lui-même**, et non une CVM ou une autre VM. Exécuter en lecture seule :

```bash
lspci -nn | grep -Ei 'Ethernet|Network'
ip -br link

for nic in /sys/class/net/*; do
  name=$(basename "$nic")
  echo "=== $name ==="
  ethtool -i "$name" 2>/dev/null | grep -E 'driver:|bus-info:'
done
```

Les résultats doivent ensuite être recoupés avec les **connecteurs physiques réels** et la configuration des cartes AIOM/OCP/PCIe. Les informations sensibles de l'environnement (hôtes, IP, MAC, numéros de série, captures BMC) doivent rester hors du dépôt public.

**Statut :** premier relevé reçu, mais non exploitable pour identifier les ports physiques ; nouvel inventaire AHV attendu.

### Deuxième relevé : sortie vide sur une machine présentée comme hôte Nutanix

Un nouveau relevé a été fourni sur une console système annoncée comme une **machine Nutanix** :

```bash
lspci -nn | grep -Ei 'Ethernet|Network'
# Aucune ligne affichée.
```

**Ce qui est constaté :** la recherche n'a trouvé aucune ligne correspondante dans la sortie de `lspci`. Cela **ne démontre pas** l'absence de carte réseau physique. Le rôle exact du système (hôte AHV, autre hyperviseur, environnement restreint) et le contenu complet de `lspci` n'ont pas été confirmés.

Pour départager les hypothèses, demander la sortie **sans détails sensibles** de :

```bash
cat /etc/os-release
lspci -nn | head -30
ip -br link

for nic in /sys/class/net/*; do
  name=$(basename "$nic")
  echo "=== $name ==="
  ethtool -i "$name" 2>/dev/null | grep -E 'driver:|bus-info:'
done
```

**Action NetBox :** ne pas ajouter de ports supposés au Device Type `NX-8170A-G10` à partir de cette sortie vide ; les interfaces et connecteurs physiques restent à confirmer.

### Troisième relevé : hôte AHV physique confirmé (inventaire PCI et pilotes)

Un relevé complémentaire a confirmé le système **Nutanix AHV 11.2**, sur une plateforme AMD Turin. Les interfaces de l'hyperviseur ont été corrélées aux fonctions PCI et aux pilotes Linux, **sans publier les identifiants de l'hôte, les adresses MAC ou les informations de topologie**.

| Interface AHV | Bus PCI | Famille de contrôleur | Pilote | Information de port |
| --- | --- | --- | --- | --- |
| `eth0` | `01:00.0` | Intel X710 for 10GBASE-T | `i40e` | Ethernet 10GBASE-T, à confirmer physiquement |
| `eth2` | `01:00.1` | Intel X710 | `i40e` | Ethernet 10GBASE-T, à confirmer physiquement |
| `eth3` | `01:00.2` | Intel X710 | `i40e` | Ethernet 10GBASE-T, à confirmer physiquement |
| `eth5` | `01:00.3` | Intel X710 | `i40e` | Ethernet 10GBASE-T, à confirmer physiquement |
| `eth1` | `12:00.0` | Broadcom, référence non identifiée | `bnxt_en` | Vitesse/connecteur non déterminés |
| `eth4` | `12:00.1` | Broadcom, référence non identifiée | `bnxt_en` | Vitesse/connecteur non déterminés |

Le contrôleur Intel `X710 for 10GBASE-T [8086:15ff]` est directement visible dans `lspci` pour `01:00.0` ; les trois autres fonctions `01:00.x` partagent le pilote `i40e`. **La présence de six interfaces Ethernet PCI est attestée**, mais la correspondance exacte avec les connecteurs externes et la nature des deux interfaces Broadcom restent à vérifier.

L'interface `bmc` utilise le pilote **`rndis_host` sur un bus USB** : il s'agit d'une interface hôte-vers-BMC ; elle ne prouve pas la présence, la vitesse ou le nombre de ports IPMI/BMC physiques accessibles à l'arrière du serveur. Les interfaces `br*`, `tap*`, `vnet*`, `ovs-system` et `vxlan*` sont des interfaces logicielles et **ne doivent pas être importées comme ports physiques de Device Type**.

**Prochain contrôle en lecture seule sur l'hôte AHV :**

```bash
lspci -nn -s 12:00.0
lspci -nn -s 12:00.1
lspci -nn -s 01:00.0
ethtool eth1 | grep -Ei 'Supported link modes|Speed:|Port:|Supported ports|Link detected'
ethtool eth4 | grep -Ei 'Supported link modes|Speed:|Port:|Supported ports|Link detected'
```

Les informations détaillées des ports Broadcom, cartes installées et prises externes devront être confirmées avec la documentation OEM ou la configuration matérielle. **Ne pas généraliser la configuration constatée à tous les exemplaires du même modèle si des options AIOM/OCP/PCIe sont possibles.**

### Quatrième relevé : contrôleur Broadcom et connectique identifiés

Le complément d'inventaire réalisé directement sur l'hôte AHV confirme **deux fonctions PCI Broadcom BCM57416 NetXtreme-E Dual-Media 10G RDMA Ethernet Controller** (`[14e4:16d8]`, révision 01). Le pilote `bnxt_en` les associe à `eth1` et `eth4`.

```text
eth1 : Broadcom BCM57416 — Port: Twisted Pair — Speed: 10000Mb/s
eth4 : Broadcom BCM57416 — Port: Twisted Pair — Speed: Unknown!
```

`eth1` était actif à 10 Gb/s ; `eth4` n'avait pas de lien et sa vitesse **n'était pas négociée**. `Speed: Unknown!` n'implique pas à lui seul une panne ou une limitation à 1 Gb/s. Les sorties filtrées de `ethtool` ne montrent que la première ligne `Supported link modes` et omettent les lignes de continuation : ne pas en déduire l'absence du mode 10 Gb/s.

**Synthèse de la configuration observée sur cet exemplaire :**

| Interfaces | Contrôleur | Nombre | Modèle NetBox candidat |
| --- | --- | ---: | --- |
| `eth0`, `eth2`, `eth3`, `eth5` | Intel X710 10GBASE-T (`i40e`) | 4 | `10gbase-t` |
| `eth1`, `eth4` | Broadcom BCM57416 Dual-Media 10G (`bnxt_en`), `Port: Twisted Pair` | 2 | `10gbase-t` |

**Conclusion :** six interfaces Ethernet physiques de type cuivre 10 GbE peuvent être proposées pour **la configuration effectivement observée** du `NX-8170A-G10-A9355-CM`. Les interfaces logicielles, l'USB RNDIS du BMC et les contrôleurs VirtIO de la CVM sont exclus. La présence d'une carte optionnelle ou d'un port BMC RJ45 externe reste à confirmer par l'inventaire physique. **Aucun changement de Device Type NetBox n'est attesté par ce relevé.**

Une future correction API doit être idempotente : uniquement ajouter les `interface-templates` absents (nom + modèle), signaler toute différence de type, simuler avant `--apply`, et ne modifier aucun autre modèle.

**Script préparé (non exécuté sur l'instance) :** [`scripts/fix_nutanix_8170a_interfaces.py`](scripts/fix_nutanix_8170a_interfaces.py). Il fait une simulation par défaut, traite seulement le Device Type `NX-8170A-G10`, ne modifie pas les interfaces déjà présentes et exige `--apply` pour créer les six interfaces. Ses paramètres API sont lus uniquement depuis l'environnement local ; la vérification TLS reste activée par défaut.

### Diagnostic du lancement de script : certificat autosigné

Lors de la **première simulation** du script ciblé `scripts/fix_nutanix_8170a_interfaces.py`, la requête HTTPS initiale a échoué :

```text
requests.exceptions.SSLError: CERTIFICATE_VERIFY_FAILED
self-signed certificate
```

L'exception s'est produite au **premier GET** de `/api/dcim/device-types/` : **aucune interface n'a été créée ou modifiée par cet essai**.

Le script a été conçu pour activer la vérification TLS par défaut, et prendre facultativement `NETBOX_CA_BUNDLE` (fichier CA monté dans le conteneur) ou `NETBOX_TLS_VERIFY=false`. En environnement de test **seulement**, l'exécution ponctuelle suivante permet de poursuivre le diagnostic :

```bash
docker compose run --rm \
  -e NETBOX_TLS_VERIFY=false \
  -v "$PWD/fix_nutanix_8170a_interfaces.py:/app/fix_nutanix_8170a_interfaces.py:ro" \
  --entrypoint python \
  netbox-library-import /app/fix_nutanix_8170a_interfaces.py
```

**Sécurité :** ce paramètre désactive la validation d'identité du serveur et expose aux attaques d'interception ; il ne doit pas devenir la configuration permanente. Installer de préférence un certificat de confiance avec **SAN correspondant au DNS ou à l'adresse IP réellement utilisée** et transmettre sa chaîne CA à l'importeur. **Aucun résultat de la seconde simulation n'est encore confirmé dans ce document.**

## 6. Procédure sûre de mise à jour NetBox

1. Faire l'inventaire exact des modèles présents et des ports manquants (`dcim/device-types/` et `dcim/interface-templates/`).
2. Pour chaque variante validée, préparer un manifeste de ports, **sans inclure les cartes optionnelles non installées**.
3. Lancer une simulation sans écritures : lister `model`, `interface`, `type`, `mgmt_only`.
4. Vérifier les doublons par ID de Device Type et par nom d'interface.
5. Sauvegarder NetBox et réaliser l'import via API ; conserver le bilan d'erreurs.
6. Vérifier dans **Devices → Device Types → Interfaces** ; attention : les nouveaux templates ne mettent **pas** automatiquement à jour les *Device Interfaces* des équipements déjà créés.
7. Si des appareils physiques préexistent, synchroniser leurs interfaces par une opération **distincte** et contrôlée ; ne jamais les effacer automatiquement.

## 7. Suivi des actions

| Action | État |
| --- | --- |
| Génération de 33 YAML Nutanix | Réalisé |
| Simulation de création des modèles et 73 composants | Réussie |
| Import Nutanix réel | Signalé terminé ; bilan détaillé à archiver |
| Identification d'un modèle sans Interfaces dans NetBox | Confirmée (`NX-8150G-G10`) |
| Simulation de 14 ports sur quatre modèles | Réussie ; création non démontrée |
| Validation des interfaces pour tous les modèles | **À faire** |
| Vérification des variantes NX-8150 | **À faire** |
| Relevé des cartes réseau pour NX-8170A-G10-A9355-CM | **Six interfaces confirmées** : 4 Intel X710 10GBASE-T + 2 Broadcom BCM57416 cuivre 10G ; import NetBox à faire |
| Images avant/arrière Nutanix | **À faire** |

## Sources de référence

- [Bibliothèque communautaire de modèles NetBox](https://github.com/netbox-community/devicetype-library)
- [NetBox — documentation Device Types](https://netboxlabs.com/docs/netbox/)
- [Nutanix — Hardware Platforms](https://www.nutanix.com/products/hardware-platforms/specsheet)
- [POC Migration2Netbox — article principal](POC-Migration2Netbox.md)

---

*Cette page distingue les résultats de simulation, les créations effectives et les caractéristiques matérielles encore à confirmer. Elle ne constitue pas une certification des 33 modèles Nutanix.*
