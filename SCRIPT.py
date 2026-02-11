import requests
import os
import subprocess
import shutil
import threading
import sys
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
BASE_URL = "http://172.22.215.130:8080" #
DOSSIER_RACINE = "donnees_sequences"
PAYS = ["PT","CH","DE","GB","CZ","FR","DK","LV","RU","HR",
        "SI","GR","IT","RO","LT","SE","ES","BE","NO","FI",
        "PL","NL","BY","LU","UA","AL","IE","AT","EE","RS",
        "HU","ME","BG","SK","MD","IS"]

# --- 1. TEST DE CONNEXION (OBLIGATOIRE) ---
print("[TEST] TEST DE CONNEXION AU SERVEUR...")
try:
    # On tente de contacter la racine de l'API
    test = requests.get(BASE_URL, timeout=5)
    print(f"[OK] Serveur joignable ! (Statut: {test.status_code})")
except Exception as e:
    print(f"[ERREUR] ERREUR FATALE : Impossible de joindre {BASE_URL}")
    print(f"   Detail : {e}")
    print("-> Verifiez que vous etes bien sur le reseau de l'universite.")
    sys.exit(1)

# Creation du dossier racine
if not os.path.exists(DOSSIER_RACINE):
    os.makedirs(DOSSIER_RACINE)

# Verrou pour Git
verrou_git = threading.Lock()

def synchroniser_et_nettoyer(code_pays, dossier_pays):
    with verrou_git:
        print(f"[GIT] Envoi securise pour {code_pays}...")
        try:
            subprocess.run(["git", "add", dossier_pays], check=True)
            subprocess.run(["git", "commit", "-m", f"Data: {code_pays}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print(f"[CLEAN] Suppression du dossier {code_pays}...")
            shutil.rmtree(dossier_pays)
        except Exception as e:
            print(f"[ERREUR] Erreur Git pour {code_pays}: {e}")

def traiter_pays(code_pays):
    dossier_pays = os.path.join(DOSSIER_RACINE, code_pays)
    if not os.path.exists(dossier_pays):
        os.makedirs(dossier_pays)
        
    print(f"[START] Thread lance pour {code_pays}...")
    fichiers_trouves = 0
    annee = 1978 # Date de depart
    
    # Boucle infinie
    while True:
        stop_pays = False
        
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            trimestre = f"{annee}{q}"
            url = f"{BASE_URL}/archived/sequences/{code_pays}/{trimestre}"
            nom_fichier = f"{code_pays}_{trimestre}.fasta"
            chemin_final = os.path.join(dossier_pays, nom_fichier)
            
            try:
                # Timeout reduit
                reponse = requests.get(url, timeout=2)
                
                # Check 1 : Futur atteint ?
                if "Too early" in reponse.text:
                    stop_pays = True
                    break
                
                # Check 2 : Succes ?
                if reponse.status_code == 200:
                    with open(chemin_final, "wb") as f:
                        f.write(reponse.content)
                    print(f"   [OK] [{code_pays}] Trouve : {trimestre}")
                    fichiers_trouves += 1
                
                # Check 3 : Erreur autre que 404
                elif reponse.status_code != 404:
                    print(f"   [INFO] [{code_pays}] Erreur HTTP {reponse.status_code} sur {trimestre}")

            except Exception as e:
                # Si erreur de connexion
                print(f"   [ERREUR] [{code_pays}] Connexion echouee sur {trimestre} : {e}")
        
        if stop_pays:
            break
        
        annee += 1
    
    if fichiers_trouves > 0:
        synchroniser_et_nettoyer(code_pays, dossier_pays)
    else:
        print(f"[INFO] [{code_pays}] Aucune donnee trouvee. Dossier nettoye.")
        try:
            os.rmdir(dossier_pays)
        except:
            pass

# --- LANCEMENT ---
print(f"--- DEMARRAGE MASSIF ({len(PAYS)} PAYS) ---")
with ThreadPoolExecutor(max_workers=len(PAYS)) as executor:
    executor.map(traiter_pays, PAYS)
print("--- TERMINE ---")
