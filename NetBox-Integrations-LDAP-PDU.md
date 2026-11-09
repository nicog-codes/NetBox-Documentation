# Intégrations étudiées — LDAP/Active Directory et Smart PDU

> **Statut :** pistes techniques discutées durant le POC Migration2Netbox, **non déployées ni validées**.  
> Ce document ne publie aucun détail de connexion à un annuaire ou à des équipements internes.

## 1. Authentification LDAP / Active Directory

**Objectif :** connecter NetBox à un annuaire **Microsoft Active Directory** pour authentifier les utilisateurs et, si souhaité, attribuer des droits selon les groupes AD.

Le backend LDAP est pris en charge par NetBox, avec **installation/configuration des dépendances LDAP** dans l'environnement applicatif selon le mode de déploiement. Il ne s'agit pas d'un module tiers fonctionnellement obligatoire, mais l'intégration peut nécessiter d'adapter la construction de l'image ou les dépendances de l'instance NetBox. Ce point est distinct du script d'import externe, qui ne nécessite aucun plugin NetBox.

Principes retenus pour un futur chantier :

- **LDAPS** avec validation du certificat du contrôleur de domaine ;
- compte de service LDAP en lecture seule et recherches limitées ;
- correspondance entre groupes AD et droits NetBox ;
- compte administrateur local conservé en secours ;
- aucun mot de passe de bind, token ou DN sensible dans un dépôt public.

**Décision :** privilégier LDAP pour une intégration AD Windows ; la configuration concrète est reportée.

Référence : [NetBox — LDAP authentication](https://netboxlabs.com/docs/netbox/en/stable/installation/6-ldap/).

## 2. Smart PDU Schleifenbauer : inventaire et consommation

**Objectif :** documenter les PDU intelligents dans NetBox et suivre leur consommation totale dans le temps.

NetBox documente les objets de distribution électrique (**Power Ports**, **Power Outlets**, **Power Feeds** et câblage), mais ne constitue pas à lui seul un système de polling périodique SNMP ni une base de séries temporelles.

Architecture envisagée :

```text
Smart PDU Schleifenbauer
          |
         SNMP
          |
 Collecteur autonome (Docker)
          |
     +----+----------------+
     |                     |
  InfluxDB / Grafana     API NetBox
  Historique W, kWh      Inventaire, lien dashboard,
                         dernière mesure facultative
```

Mesures envisagées, **selon le modèle et ses MIB** : puissance instantanée (W), énergie (kWh), courant (A), tension (V), mesures par phase et éventuellement par prise.

Pistes étudiées :

- collecteur SNMP (par exemple Telegraf) vers InfluxDB/Grafana ;
- champs personnalisés NetBox mis à jour via l'API, si souhaité ;
- association par baie / PDU / phase et alarmes de puissance ;
- SNMPv3 si les équipements le permettent ;
- distinction entre une prise alimentée, une prise mesurée et l'identité réelle du serveur branché : **une mesure de consommation n'identifie pas automatiquement le serveur**.

**Statut :** aucune configuration SNMP, aucun OID de MIB et aucun tableau de bord de production n'ont été validés. Identifier d'abord la génération exacte des PDU et leur mode d'adressage (unité indépendante ou bridge).

Références :

- [Documentation NetBox](https://netboxlabs.com/docs/netbox/)
- [Schleifenbauer — support](https://www.schleifenbauer.eu/)

## 3. Règles générales du POC

- Séparer **documentation d'inventaire** (NetBox), **télémétrie** (collecteur/TSDB) et **authentification** (annuaire).
- Préserver les sauvegardes et la maintenance du NetBox existant.
- Tester en mode lecture seule / simulation avant toute écriture.
- Ne pas publier d'information d'identification ni de topologie interne.
- Présenter explicitement les résultats **simulés**, **déployés** et **en attente**.

---

*Document public de planification. Les implémentations futures devront être testées et documentées séparément.*
