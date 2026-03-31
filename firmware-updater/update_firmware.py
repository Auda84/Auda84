#!/usr/bin/env python3
"""
=============================================================================
RMA Research Network — Script de mise à jour firmware OmniSwitch AOS
=============================================================================
Compatibilité : OmniSwitch 6450 / 6860 (AOS 6.x / 8.x)
Transport     : SCP (transfert fichier) + SSH (commandes CLI)
Authentification : Login / Mot de passe
Résultats     : Fichier CSV horodaté + push automatique vers GitHub

Dépendances Python :
    pip install paramiko scp gitpython

Utilisation :
    python update_firmware.py                    # mise à jour complète
    python update_firmware.py --dry-run          # vérification versions seulement
    python update_firmware.py --no-reboot        # copie firmware sans rebooter
    python update_firmware.py --no-git           # ne pas pusher vers git
=============================================================================
"""

import argparse
import configparser
import csv
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import paramiko
from scp import SCPClient
import git  # gitpython

# =============================================================================
# CONFIGURATION DU LOGGER
# =============================================================================
# Affiche les logs dans le terminal ET dans un fichier update.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("update.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# =============================================================================
# LECTURE DE LA CONFIGURATION
# =============================================================================
def load_config(config_path: str = "config.ini") -> configparser.ConfigParser:
    """
    Charge le fichier config.ini.
    Lève une erreur explicite si le fichier est absent.
    """
    if not Path(config_path).exists():
        log.error(f"Fichier de configuration introuvable : {config_path}")
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    return cfg


# =============================================================================
# LECTURE DE LA LISTE DES SWITCHES (CSV)
# =============================================================================
def load_switches(csv_path: str) -> list[dict]:
    """
    Lit le fichier CSV contenant la liste des switches.

    Format attendu (avec en-tête) :
        ip,name,model,enabled
        10.67.242.10,CoreSw-K,OS6860,yes
        10.67.242.20,CoreSw-M,OS6450,yes

    Retourne une liste de dicts. Les lignes avec enabled=no sont ignorées.
    """
    if not Path(csv_path).exists():
        log.error(f"Fichier switches introuvable : {csv_path}")
        sys.exit(1)

    switches = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ignorer les lignes désactivées ou vides
            if row.get("enabled", "yes").strip().lower() != "yes":
                log.info(f"Switch ignoré (disabled) : {row.get('ip')} — {row.get('name')}")
                continue
            if not row.get("ip", "").strip():
                continue
            switches.append({
                "ip":    row["ip"].strip(),
                "name":  row.get("name", "").strip(),
                "model": row.get("model", "").strip(),
            })

    log.info(f"{len(switches)} switch(es) chargé(s) depuis {csv_path}")
    return switches


# =============================================================================
# CONNEXION SSH
# =============================================================================
def ssh_connect(ip: str, username: str, password: str, timeout: int = 15) -> paramiko.SSHClient:
    """
    Ouvre une connexion SSH vers un switch OmniSwitch.
    Retourne le client SSH ou lève une exception en cas d'échec.
    """
    client = paramiko.SSHClient()
    # Accepte automatiquement les clés SSH inconnues (réseau interne RMA)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=ip,
        username=username,
        password=password,
        timeout=timeout,
        look_for_keys=False,   # pas de clé SSH, uniquement mot de passe
        allow_agent=False,
    )
    return client


# =============================================================================
# RÉCUPÉRATION DE LA VERSION FIRMWARE COURANTE
# =============================================================================
def get_current_version(client: paramiko.SSHClient) -> str:
    """
    Exécute 'show microcode' sur le switch et extrait la version AOS.

    Exemple de sortie AOS :
        Package           Release          Size     Description
        ----------------  ---------------  -------  -----------
        Tos.img           6.7.2.R06        ...      Alcatel-Lucent OS

    Retourne la version sous forme de string (ex. "6.7.2.R06")
    ou "UNKNOWN" si la commande échoue.
    """
    try:
        _, stdout, _ = client.exec_command("show microcode", timeout=20)
        output = stdout.read().decode("utf-8", errors="replace")

        # Chercher une ligne contenant un numéro de version AOS (pattern X.Y.Z.RXX)
        for line in output.splitlines():
            parts = line.split()
            for part in parts:
                # Versions AOS 6.x : "6.7.2.R06" — AOS 8.x : "8.9.1.R01"
                if part.count(".") >= 2 and part[0].isdigit():
                    return part
        return "UNKNOWN"
    except Exception as e:
        log.warning(f"Impossible de lire la version : {e}")
        return "ERROR"


# =============================================================================
# TRANSFERT DU FIRMWARE VIA SCP
# =============================================================================
def upload_firmware(client: paramiko.SSHClient, local_firmware: str, remote_path: str) -> bool:
    """
    Copie le fichier firmware vers le switch via SCP.

    Sur OmniSwitch AOS 6.x : destination typique = /flash/working/
    Sur OmniSwitch AOS 8.x : destination typique = /flash/working/

    Retourne True si succès, False sinon.
    """
    try:
        log.info(f"  → Upload SCP : {local_firmware} vers {remote_path}")
        with SCPClient(client.get_transport()) as scp:
            scp.put(local_firmware, remote_path=remote_path)
        log.info("  ✓ Transfert SCP terminé")
        return True
    except Exception as e:
        log.error(f"  ✗ Échec SCP : {e}")
        return False


# =============================================================================
# REBOOT DU SWITCH
# =============================================================================
def reboot_switch(client: paramiko.SSHClient, reload_delay: int = 5) -> bool:
    """
    Lance un reboot du switch via la commande 'reload' (AOS 6.x)
    ou 'reload from working no rollback-timeout' (AOS 8.x).

    Le switch va couper la connexion SSH — c'est normal.
    Retourne True si la commande a bien été envoyée.
    """
    try:
        log.info("  → Envoi commande reboot...")
        # Commande compatible AOS 6.x et 8.x
        # 'reload' redémarre depuis la partition 'working'
        client.exec_command("reload", timeout=10)
        time.sleep(reload_delay)  # laisser le temps au switch d'initier le reboot
        log.info("  ✓ Commande reboot envoyée")
        return True
    except Exception as e:
        # Une exception ici est souvent normale (connexion coupée par le switch)
        log.info(f"  ✓ Reboot initié (connexion coupée : {e})")
        return True


# =============================================================================
# VÉRIFICATION DE LA VERSION POST-REBOOT
# =============================================================================
def wait_and_verify(
    ip: str,
    username: str,
    password: str,
    expected_version: str,
    max_wait: int = 300,
    poll_interval: int = 30,
) -> str:
    """
    Attend que le switch redémarre puis vérifie la nouvelle version firmware.

    - max_wait      : temps maximum d'attente en secondes (défaut 5 min)
    - poll_interval : intervalle entre chaque tentative de reconnexion

    Retourne la version détectée après reboot, ou "TIMEOUT" / "ERROR".
    """
    log.info(f"  → Attente du reboot ({max_wait}s max)...")
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        log.info(f"  ... {elapsed}s écoulées, tentative de reconnexion vers {ip}")

        try:
            client = ssh_connect(ip, username, password, timeout=10)
            new_version = get_current_version(client)
            client.close()

            log.info(f"  ✓ Reconnexion OK — version détectée : {new_version}")
            return new_version

        except Exception:
            log.info(f"  ... switch pas encore disponible, nouvelle tentative dans {poll_interval}s")

    log.warning(f"  ✗ Timeout atteint ({max_wait}s) — switch {ip} non joignable")
    return "TIMEOUT"


# =============================================================================
# TRAITEMENT D'UN SWITCH (fonction principale par équipement)
# =============================================================================
def process_switch(
    switch: dict,
    cfg: configparser.ConfigParser,
    dry_run: bool,
    do_reboot: bool,
) -> dict:
    """
    Gère la mise à jour complète d'un switch :
      1. Connexion SSH
      2. Lecture version courante
      3. Comparaison avec version cible
      4. Upload firmware si nécessaire
      5. Reboot si demandé
      6. Vérification post-reboot

    Retourne un dict de résultat qui sera écrit dans le CSV de rapport.
    """
    ip      = switch["ip"]
    name    = switch["name"]
    model   = switch["model"]

    # Paramètres depuis config.ini
    username        = cfg["credentials"]["username"]
    password        = cfg["credentials"]["password"]
    target_version  = cfg["firmware"]["target_version"]
    firmware_file   = cfg["firmware"]["local_file"]
    remote_path     = cfg["firmware"]["remote_path"]
    max_wait        = int(cfg["firmware"].get("reboot_wait_seconds", 300))

    # Résultat par défaut
    result = {
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip":              ip,
        "name":            name,
        "model":           model,
        "version_before":  "N/A",
        "version_after":   "N/A",
        "action":          "none",
        "status":          "pending",
        "notes":           "",
    }

    log.info(f"\n{'='*60}")
    log.info(f"Switch : {name} ({ip}) — {model}")
    log.info(f"{'='*60}")

    # ---- 1. Connexion SSH ----
    try:
        client = ssh_connect(ip, username, password)
        log.info(f"  ✓ Connexion SSH établie")
    except Exception as e:
        log.error(f"  ✗ Connexion SSH échouée : {e}")
        result["status"] = "ERREUR_SSH"
        result["notes"]  = str(e)
        return result

    # ---- 2. Version courante ----
    current_version = get_current_version(client)
    result["version_before"] = current_version
    log.info(f"  Version courante  : {current_version}")
    log.info(f"  Version cible     : {target_version}")

    # ---- 3. Comparaison ----
    if current_version == target_version:
        log.info("  ✓ Firmware déjà à jour — aucune action nécessaire")
        result["status"] = "A_JOUR"
        result["action"] = "none"
        client.close()
        return result

    if dry_run:
        log.info("  [DRY-RUN] Mise à jour nécessaire mais non effectuée")
        result["status"] = "DRY_RUN"
        result["action"] = "none"
        result["notes"]  = f"Mise à jour requise : {current_version} → {target_version}"
        client.close()
        return result

    # ---- 4. Upload firmware ----
    if not Path(firmware_file).exists():
        log.error(f"  ✗ Fichier firmware introuvable : {firmware_file}")
        result["status"] = "ERREUR_FIRMWARE_ABSENT"
        client.close()
        return result

    upload_ok = upload_firmware(client, firmware_file, remote_path)
    if not upload_ok:
        result["status"] = "ERREUR_UPLOAD"
        client.close()
        return result

    result["action"] = "firmware_copie"

    # ---- 5. Reboot ----
    if do_reboot:
        reboot_switch(client)
        result["action"] = "firmware_copie+reboot"
        try:
            client.close()
        except Exception:
            pass  # connexion déjà coupée par le reboot

        # ---- 6. Vérification post-reboot ----
        new_version = wait_and_verify(ip, username, password, target_version, max_wait)
        result["version_after"] = new_version

        if new_version == target_version:
            result["status"] = "SUCCES"
        elif new_version == "TIMEOUT":
            result["status"] = "TIMEOUT_REBOOT"
        else:
            result["status"] = f"VERSION_INATTENDUE ({new_version})"
    else:
        log.info("  [NO-REBOOT] Firmware copié — reboot manuel requis")
        result["status"] = "FIRMWARE_COPIE_SANS_REBOOT"
        result["notes"]  = "Reboot manuel requis pour activer le firmware"
        client.close()

    return result


# =============================================================================
# SAUVEGARDE DU RAPPORT CSV
# =============================================================================
def save_report(results: list[dict], output_dir: str = "reports") -> str:
    """
    Écrit les résultats dans un fichier CSV horodaté dans le dossier 'reports/'.
    Retourne le chemin du fichier créé.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = Path(output_dir) / f"firmware_update_{timestamp}.csv"

    fieldnames = [
        "timestamp", "ip", "name", "model",
        "version_before", "version_after",
        "action", "status", "notes",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    log.info(f"\n✓ Rapport sauvegardé : {filename}")
    return str(filename)


# =============================================================================
# PUSH VERS GITHUB
# =============================================================================
def push_to_github(report_file: str, cfg: configparser.ConfigParser):
    """
    Ajoute le rapport CSV au dépôt Git local cloné et pousse vers GitHub.

    Le dépôt doit déjà être cloné localement (voir config.ini → [git] → repo_path).
    Le token GitHub est utilisé pour l'authentification HTTPS.
    """
    repo_path      = cfg["git"]["repo_path"]
    github_token   = cfg["git"]["token"]
    github_url     = cfg["git"]["repo_url"]
    target_subdir  = cfg["git"].get("target_subdir", "firmware-reports")

    # Chemin de destination dans le repo
    dest_dir  = Path(repo_path) / target_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / Path(report_file).name

    # Copier le rapport dans le repo local
    import shutil
    shutil.copy(report_file, dest_file)
    log.info(f"  → Rapport copié vers : {dest_file}")

    try:
        repo = git.Repo(repo_path)

        # Configurer l'URL avec le token pour l'authentification
        auth_url = github_url.replace("https://", f"https://{github_token}@")
        repo.remote("origin").set_url(auth_url)

        # Ajouter et committer
        repo.index.add([str(dest_file)])
        commit_msg = f"[firmware] Rapport mise à jour {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        repo.index.commit(commit_msg)

        # Push
        origin = repo.remote("origin")
        push_result = origin.push()
        log.info(f"  ✓ Push GitHub réussi : {commit_msg}")

    except Exception as e:
        log.error(f"  ✗ Échec push GitHub : {e}")


# =============================================================================
# AFFICHAGE DU RÉSUMÉ FINAL
# =============================================================================
def print_summary(results: list[dict]):
    """Affiche un tableau récapitulatif dans le terminal."""
    log.info(f"\n{'='*70}")
    log.info("RÉSUMÉ DE LA MISE À JOUR")
    log.info(f"{'='*70}")
    log.info(f"{'IP':<18} {'Nom':<16} {'Avant':<14} {'Après':<14} {'Statut'}")
    log.info(f"{'-'*70}")
    for r in results:
        log.info(
            f"{r['ip']:<18} {r['name']:<16} {r['version_before']:<14} "
            f"{r['version_after']:<14} {r['status']}"
        )
    log.info(f"{'='*70}")

    # Comptage par statut
    from collections import Counter
    counts = Counter(r["status"] for r in results)
    log.info(f"Total : {len(results)} switch(es)")
    for status, count in counts.items():
        log.info(f"  {status} : {count}")


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def main():
    # ---- Parsing des arguments CLI ----
    parser = argparse.ArgumentParser(
        description="Mise à jour firmware OmniSwitch RMA Research Network"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Vérifier les versions sans effectuer de mise à jour",
    )
    parser.add_argument(
        "--no-reboot",
        action="store_true",
        help="Copier le firmware sans rebooter les switches",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Ne pas pousser le rapport vers GitHub",
    )
    parser.add_argument(
        "--config",
        default="config.ini",
        help="Chemin vers le fichier de configuration (défaut : config.ini)",
    )
    parser.add_argument(
        "--switches",
        default="switches.csv",
        help="Chemin vers le fichier CSV des switches (défaut : switches.csv)",
    )
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("RMA Firmware Updater — OmniSwitch AOS")
    log.info(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        log.info("MODE : DRY-RUN (aucune modification ne sera effectuée)")
    log.info("=" * 60)

    # ---- Chargement config et liste switches ----
    cfg      = load_config(args.config)
    switches = load_switches(args.switches)

    if not switches:
        log.error("Aucun switch à traiter. Vérifiez le fichier switches.csv")
        sys.exit(1)

    # ---- Traitement de chaque switch ----
    results = []
    for switch in switches:
        result = process_switch(
            switch,
            cfg,
            dry_run=args.dry_run,
            do_reboot=not args.no_reboot,
        )
        results.append(result)

    # ---- Rapport ----
    print_summary(results)
    report_file = save_report(results)

    # ---- Push Git ----
    if not args.no_git:
        log.info("\n→ Push du rapport vers GitHub...")
        push_to_github(report_file, cfg)
    else:
        log.info("\n[--no-git] Push GitHub ignoré")

    log.info("\n✓ Script terminé.")


if __name__ == "__main__":
    main()
