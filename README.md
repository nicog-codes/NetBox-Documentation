# NetBox Documentation

Documentation technique publique consacrée à l'inventaire matériel et à l'importation de bibliothèques de *Device Types* dans NetBox.

## Articles

- [POC Migration2Netbox — Import HPE, Cisco et Nutanix](POC-Migration2Netbox.md) : architecture générique, résultats de l'import, images, diagnostic API et correction d'un problème de liaison des ports d'alimentation.
- [Nutanix — modèles YAML et interfaces réseau](Nutanix-Device-Types-Interfaces.md) : simulations, différences de modèles, résultat VirtIO de la CVM et inventaire AHV à poursuivre.
- [Intégrations à étudier — LDAP/AD et PDU](NetBox-Integrations-LDAP-PDU.md) : feuille de route d'authentification et de supervision électrique, non encore déployée.

- [Migration Asset vers Device Types](Migration-Asset-vers-Device-Types.md) : méthode générique de tri et de rapprochement d'un inventaire matériel, sans données sensibles.

## Confidentialité

Le contenu est volontairement anonymisé : aucune adresse IP privée, aucun nom d'hôte personnel, aucun token API, mot de passe, empreinte de certificat ou détail de topologie interne n'est publié.

## Références

- [NetBox](https://github.com/netbox-community/netbox)
- [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library)

## Avertissement

Les exemples sont issus d'un POC et doivent être vérifiés avant utilisation sur un environnement de production. Les modèles Nutanix générés pour l'étude sont provisoires et ne constituent pas des définitions officielles du constructeur.
