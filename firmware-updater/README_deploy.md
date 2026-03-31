# Guide de déploiement — RMA Firmware Updater

## Structure des fichiers

```
firmware-updater/
├── update_firmware.py   ← script principal
├── config.ini           ← configuration (credentials, chemins, git)
├── switches.csv         ← liste des switches à mettre à jour
├── .gitignore           ← protège config.ini et les logs
├── firmware/            ← dossier où placer le fichier .img
│   └── Tos.img          ← fichier firmware (à placer manuellement)
└── reports/             ← rapports CSV générés automatiquement
```

---

## Étape 1 — Prérequis système

### Python 3.10 ou supérieur requis

Vérifier ta version :
```bash
python --version
```

Si Python n'est pas installé : https://www.python.org/downloads/

---

## Étape 2 — Installer les dépendances

Ouvre un terminal dans le dossier `firmware-updater/` et exécute :

```bash
pip install paramiko scp gitpython
```

> **Sur Linux/Mac**, utilise `pip3` si `pip` ne fonctionne pas.

---

## Étape 3 — Configurer `config.ini`

Ouvre `config.ini` et remplis les champs :

```ini
[credentials]
username = admin
password = TON_MOT_DE_PASSE_SWITCH

[firmware]
target_version = 6.7.2.R06        # version à déployer
local_file = firmware/Tos.img      # chemin local du fichier firmware
remote_path = /flash/working/      # destination sur le switch
reboot_wait_seconds = 300          # attente post-reboot (5 min)

[git]
repo_path = C:\Users\toi\repos\Auda84    # chemin local du repo cloné
repo_url  = https://github.com/Auda84/Auda84.git
token     = ghp_xxxxxxxxxxxxxx           # ton Personal Access Token
target_subdir = firmware-reports         # sous-dossier dans le repo
```

> ⚠️ `config.ini` est dans `.gitignore` — il ne sera **jamais** envoyé sur GitHub.

---

## Étape 4 — Préparer le fichier firmware

1. Télécharge le fichier `.img` depuis le portail Alcatel-Lucent Enterprise (ALE)
2. Place-le dans le dossier `firmware/` :

```
firmware-updater/
└── firmware/
    └── Tos.img       ← fichier AOS 6.x
    # ou
    └── Tos8.img      ← fichier AOS 8.x
```

---

## Étape 5 — Préparer `switches.csv`

Édite `switches.csv` avec la liste de tes switches :

```csv
ip,name,model,enabled
10.67.242.10,CoreSw-K,OS6860,yes
10.67.242.20,CoreSw-M,OS6860,yes
10.67.243.30,AccSw-C01,OS6450,no    ← ignoré (enabled=no)
```

- `enabled = no` → switch ignoré lors de l'exécution
- `model` → informatif, utilisé dans le rapport CSV

---

## Étape 6 — Cloner ton dépôt Git en local

Si ce n'est pas déjà fait :

```bash
git clone https://github.com/Auda84/Auda84.git
```

Puis mettre à jour `config.ini` → `repo_path` avec le chemin absolu du dossier cloné.

---

## Utilisation du script

### Vérification des versions (sans rien modifier)
```bash
python update_firmware.py --dry-run
```
→ Se connecte à chaque switch, lit la version courante, compare avec la cible. Aucune action.

### Mise à jour complète (copie + reboot + vérification)
```bash
python update_firmware.py
```

### Copie firmware sans reboot (reboot manuel ensuite)
```bash
python update_firmware.py --no-reboot
```

### Mise à jour sans push Git
```bash
python update_firmware.py --no-git
```

### Combinaison d'options
```bash
python update_firmware.py --dry-run --no-git
python update_firmware.py --no-reboot --no-git
```

---

## Résultats

### Terminal
Le script affiche en temps réel l'avancement avec un résumé final :

```
======================================================================
RÉSUMÉ DE LA MISE À JOUR
======================================================================
IP               Nom              Avant          Après          Statut
----------------------------------------------------------------------
10.67.242.10     CoreSw-K         6.7.1.R03      6.7.2.R06      SUCCES
10.67.242.20     CoreSw-M         6.7.2.R06      N/A            A_JOUR
10.67.243.10     AccSw-B01        6.7.1.R03      6.7.2.R06      SUCCES
======================================================================
```

### Fichier CSV (rapport)
Un fichier `reports/firmware_update_YYYYMMDD_HHMMSS.csv` est créé automatiquement.

| Colonne | Description |
|---|---|
| timestamp | Date/heure de l'opération |
| ip | Adresse IP du switch |
| name | Nom du switch |
| model | Modèle |
| version_before | Version avant mise à jour |
| version_after | Version après reboot |
| action | Action effectuée |
| status | SUCCES / A_JOUR / ERREUR_SSH / TIMEOUT_REBOOT / DRY_RUN |
| notes | Informations complémentaires |

### GitHub
Le rapport CSV est automatiquement poussé dans :
```
Auda84/
└── firmware-reports/
    └── firmware_update_20260330_143022.csv
```

---

## Statuts possibles

| Statut | Signification |
|---|---|
| `SUCCES` | Firmware mis à jour et vérifié après reboot |
| `A_JOUR` | Firmware déjà à la version cible |
| `DRY_RUN` | Vérification uniquement, mise à jour requise |
| `FIRMWARE_COPIE_SANS_REBOOT` | Copie OK, reboot manuel requis |
| `ERREUR_SSH` | Impossible de se connecter au switch |
| `ERREUR_UPLOAD` | Échec du transfert SCP |
| `ERREUR_FIRMWARE_ABSENT` | Fichier .img introuvable en local |
| `TIMEOUT_REBOOT` | Switch non joignable après reboot (dans le délai) |
| `VERSION_INATTENDUE` | Version après reboot différente de la cible |

---

## Dépannage

**`ModuleNotFoundError: No module named 'paramiko'`**
→ Exécuter `pip install paramiko scp gitpython`

**`Connection refused` ou `Timeout` sur un switch**
→ Vérifier que SSH est bien activé sur le switch :
```
ssh login admin password
```

**`Authentication failed`**
→ Vérifier `username` / `password` dans `config.ini`

**`FileNotFoundError: firmware/Tos.img`**
→ Placer le fichier firmware dans le sous-dossier `firmware/`

**Switch ne répond plus après reboot**
→ Augmenter `reboot_wait_seconds` dans `config.ini` (essayer 420 ou 600)

---

## Sécurité

- `config.ini` ne doit **jamais** être partagé ni commité sur Git
- Le token GitHub doit avoir uniquement les droits `repo` (pas admin)
- Régénérer le token régulièrement (tous les 90 jours)
- Sur un réseau de production, préférer les clés SSH aux mots de passe

---

*RMA Research Network — Administrateur réseau*
