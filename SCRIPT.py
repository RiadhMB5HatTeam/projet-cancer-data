import requests
import os
import subprocess
import shutil
import sys
import time

# --- CONFIGURATION ---
BASE_URL = "http://172.22.215.130:8080"
DOSSIER_RACINE = "donnees_sequences"
PAYS = ["PT","CH","DE","GB","CZ","FR","DK","LV","RU","HR",
        "SI","GR","IT","RO","LT","SE","ES","BE","NO","FI",
        "PL","NL","BY","LU","UA","AL","IE","AT","EE","RS",
        "HU","ME","BG","SK","MD","IS"]

# --- SETUP GIT ---
print("[SETUP] Configuration du cache mot de passe Git (1 heure)...")
subprocess.run(["git", "config", "credential.helper", "cache --timeout=3600"])

if not os.path.exists(DOSSIER_RACINE):
    os.makedirs(DOSSIER_RACINE)

def traiter_pays(code_pays):
    dossier_pays = os.path.join(DOSSIER_RACINE, code_pays)
    
    # On s'assure que le dossier est vide au depart
    if os.path.exists(dossier_pays):
        shutil.rmtree(dossier_pays)
    os.makedirs(dossier_pays)
        
    print(f"\n[START] Traitement de {code_pays} (Mode Sequentiel)...")
    fichiers_trouves = 0
    
    # SCAN DE 1978 A 2029
    for annee in range(1978, 2029):
        stop_pays = False
        
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            trimestre = f"{annee}{q}"
            url = f"{BASE_URL}/archived/sequences/{code_pays}/{trimestre}"
            nom_fichier = f"{code_pays}_{trimestre}.fasta"
            chemin_final = os.path.join(dossier_pays, nom_fichier)
            
            try:
                reponse = requests.get(url, timeout=2)
                
                # Verification d'arret (Futur ou 404 apres 2022)
                if "Too early" in reponse.text or reponse.status_code == 404:
                    if annee > 2022:
                        stop_pays = True
                        break
                
                # Succes (200 OK)
                if reponse.status_code == 200:
                    with open(chemin_final, "wb") as f:
                        f.write(reponse.content)
                    print(f"   [OK] {code_pays} {trimestre}")
                    fichiers_trouves += 1
            
            except Exception as e:
                # Si erreur de quota disque, on arrete tout
                if "Disk quota exceeded" in str(e):
                    print("[FATAL] DISQUE PLEIN ! ARRET D'URGENCE.")
                    sys.exit(1)
                pass
        
        if stop_pays:
            break

    # FIN DU PAYS : ENVOI ET NETTOYAGE
    if fichiers_trouves > 0:
        print(f"[GIT] Envoi de {code_pays} sur GitHub...")
        try:
            subprocess.run(["git", "add", dossier_pays], check=True)
            subprocess.run(["git", "commit", "-m", f"Data: {code_pays}"], check=False)
            
            push = subprocess.run(["git", "push", "origin", "main"], check=True)
            
            if push.returncode == 0:
                print(f"[DELETE] Suppression locale de {code_pays}...")
                shutil.rmtree(dossier_pays) # Suppression immediate
                print(f"[CLEAN] Espace libere. Pret pour le suivant.")
            else:
                print("[ERREUR] Le push a echoue, fichiers conserves.")
                
        except Exception as e:
            print(f"[ERREUR GIT] : {e}")
    else:
        print(f"[VIDE] Rien trouve pour {code_pays}. Nettoyage.")
        shutil.rmtree(dossier_pays)

# --- LANCEMENT ---
print("--- DEMARRAGE SEQUENTIEL ---")

# On fait les pays UN PAR UN pour ne pas saturer le disque
for pays in PAYS:
    traiter_pays(pays)

print("--- TERMINE ---")
