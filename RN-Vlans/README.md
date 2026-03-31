# RN-Vlans — Documentation du réseau RMA Research Network

## Description

Ce fichier Excel documente la configuration VLAN de l'infrastructure LAN du **Research Network** de l'Académie Royale Militaire (RMA). Il recense les VLANs actifs et désactivés ainsi que leur présence sur chaque switch de cœur et d'agrégation.

---

## Contenu du fichier `RN-Vlans-formatted.xlsx`

### Onglet `VLANs`

Tableau principal de référence. Chaque ligne correspond à un VLAN et indique, pour chaque équipement :

| Colonne | Description |
|---|---|
| **VLAN** | Identifiant du VLAN (ex. 5, 21, 1000) |
| **DistSw / Description** | Bâtiment ou usage associé + IP du DistSw |
| **Enabled** | VLAN activé (`yes`) ou désactivé (`no`) sur ce switch |
| **Port** | Port(s) untagged associé(s) |
| **IP** | Adresse IP de l'interface SVI du switch |
| **Linkagg** | Agrégats de liens (LAG) portant le VLAN (tagged) |
| **Spantree** | Mode et priorité Spanning Tree |
| **VRRP** | Adresse IP virtuelle VRRP et priorité |

**Code couleur :**
- 🟩 Vert clair → VLAN `enabled` sur ce switch
- 🟥 Orange clair → VLAN `disabled` sur ce switch
- 🟨 Jaune → Colonne VLAN ID

---

### Onglet `CoreSw Topology`

Liens inter-switches (linkagg) entre les équipements de cœur :

| Switch | Linkagg | Destination | Port |
|---|---|---|---|
| CoreSw K | linkagg 10 | CoreSw M | 2/1/31 |
| CoreSw K | linkagg 40 | CoreSw D0 | 1/1/32 |
| CoreSw M | linkagg 10 | CoreSw K | 1/1/31 |
| CoreSw M | linkagg 20 | CoreSw L | 2/1/32 |
| CoreSw L | linkagg 20 | CoreSw M | 1/1/32 |
| CoreSw L | linkagg 30 | CoreSw D0 | 2/1/31 |
| CoreSw L | linkagg 33 | AggrSw H | 1/1/29 |
| AggrSw H | linkagg 33 | CoreSw L | 1/1/29 |
| CoreSw D0 | linkagg 30 | CoreSw L | 1/1/31 |
| CoreSw D0 | linkagg 40 | CoreSw K | 2/1/32 |

---

### Onglet `Addresses`

Liste complète des adresses IP utilisées dans l'infrastructure (interfaces SVI, VRRP, management).

---

### Onglet `Ping Tests`

Tableau de tests de connectivité. Contient les commandes ping générées automatiquement vers les adresses `.5` de chaque sous-réseau VLAN, avec correspondance vers les informations de chaque switch.

---

## Équipements référencés

| Équipement | Rôle | Plage IP management |
|---|---|---|
| **CoreSw K** | Switch de cœur K | 10.67.242.10 |
| **CoreSw L** | Switch de cœur L | 10.67.242.30 |
| **CoreSw D0** | Switch de cœur D | 10.67.242.40 |
| **CoreSw M** | Switch de cœur M | 10.67.242.20 |
| **AggrSw H** | Switch d'agrégation H | 10.67.242.33 |

---

## VLANs actifs (résumé)

| VLAN | Description | Subnet |
|---|---|---|
| 5 | SRVKMS | 10.67.1.0/24 |
| 10 | Bâtiment A | 10.67.10.0/24 |
| 21 | Bâtiment B / C basement | 10.67.21.0/24 |
| 31 | Bâtiment C2 | 10.67.31.0/24 |
| 40 | Bâtiment D0 | 10.67.40.0/24 |
| 41–44 | Bâtiments D1–D-1 | 10.67.41–44.0/24 |
| 50–51 | Bâtiment E | 10.67.50–51.0/24 |
| 61 | Bâtiment F1 | 10.67.61.0/24 |
| 70–71 | Bâtiment G15 | 10.67.70–71.0/24 |
| 80–84 | Bâtiment H1 | 10.67.80–84.0/24 |
| 90 | Bâtiment I-1 | 10.67.90.0/24 |
| 110–114 | Bâtiment K | 10.67.110–114.0/24 |
| 151–152 | Bâtiment O-1 | 10.67.151–152.0/24 |
| 171–172 | Bâtiment Q-1 | 10.67.171–172.0/24 |
| 184 | À vérifier | 10.67.184.0/24 |
| 190 | À vérifier | 10.67.190.0/24 |
| 200 | K-2 Firewall | 10.67.200.0/24 |
| 250 | D XSIC | 10.67.250.0/24 |
| 1000 | Management switches (legacy) | 10.67.242.0/24 |
| 1001 | Management switches (nouveaux) | 10.67.243.0/24 |

---

## Notes

- Les VLANs **sans DistSw** sont des VLANs désactivés réservés ou non encore déployés.
- Les entrées marquées `check !` nécessitent une vérification de configuration.
- VRRP : priorité **200** = master sur CoreSw K, priorité **100** = backup sur CoreSw L.
- Le VLAN **1** est de gestion interne (Spantree désactivé sur tous les switches).

---

*Dernière mise à jour : 2026-03-30*  
*Maintenu par : Administrateur réseau RMA*
