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

# --- 1. CONFIGURATION GIT (Cache mot de passe) ---
print("[SETUP] Configuration du cache Git...")
subprocess.run(["git", "config", "credential.helper", "cache --timeout=3600"])

if not os.path.exists(DOSSIER_RACINE):
    os.makedirs(DOSSIER_RACINE)

def traiter_et_nettoyer_un_pays(code_pays):
    dossier_pays = os.path.join(DOSSIER_RACINE, code_pays)
    
    # Nettoyage préventif au cas où
    if os.path.exists(dossier_pays):
        shutil.rmtree(dossier_pays)
    os.makedirs(dossier_pays)
        
    print(f"\n\uD83D\uDE80 [START] Traitement de {code_pays} (Mode Séquentiel)...")
    fichiers_trouves = 0
    
    # SCAN 1978 -> 2028
    for annee in range(1978, 2029):
        stop_pays = False
        
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            trimestre = f"{annee}{q}"
            url = f"{BASE_URL}/archived/sequences/{code_pays}/{trimestre}"
            nom_fichier = f"{code_pays}_{trimestre}.fasta"
            chemin_final = os.path.join(dossier_pays, nom_fichier)
            
            try:
                # Requete
                reponse = requests.get(url, timeout=2)
                
                # Arret si futur ou 404
                if "Too early" in reponse.text or reponse.status_code == 404:
                    if annee > 2022:
                        stop_pays = True
                        break
                
                # Succès
                if reponse.status_code == 200:
                    with open(chemin_final, "wb") as f:
                        f.write(reponse.content)
                    print(f"   \uD83D\uDCC4 [OK] {code_pays} {trimestre}")
                    fichiers_trouves += 1
            
            except Exception as e:
                # Si le disque est plein, on arrête TOUT immédiatement
                if "Disk quota exceeded" in str(e):
                    print("❌ ❌ ❌ DISQUE PLEIN ! ARRET D'URGENCE.")
                    sys.exit(1)
                pass
        
        if stop_pays:
            break

    # FIN DU SCAN POUR CE PAYS -> ON ENVOIE ET ON VIDE
    if fichiers_trouves > 0:
        print(f"\uD83D\uDD12 [GIT] Envoi de {code_pays} sur GitHub...")
        try:
            subprocess.run(["git", "add", dossier_pays], check=True)
            subprocess.run(["git", "commit", "-m", f"Data: {code_pays}"], check=False)
            
            push = subprocess.run(["git", "push", "origin", "main"], check=True)
            
            if push.returncode == 0:
                print(f"\uD83D\uDD25 [DELETE] Suppression locale de {code_pays}...")
                shutil.rmtree(dossier_pays) # ON SUPPRIME POUR FAIRE DE LA PLACE
                print(f"✨ Espace libéré. Prêt pour le suivant.")
                
        except Exception as e:
            print(f"❌ ERREUR GIT : {e}")
    else:
        print(f"⚠️ [VIDE] Rien trouvé pour {code_pays}. Nettoyage.")
        shutil.rmtree(dossier_pays)

# --- BOUCLE PRINCIPALE (UN PAR UN) ---
print("--- DÉMARRAGE SÉQUENTIEL (Anti-Crash Disque) ---")
for pays in PAYS:
    traiter_et_nettoyer_un_pays(pays)
    # On passe au suivant SEULEMENT quand le précédent est supprimé

print("--- TERMINÉ ---")
