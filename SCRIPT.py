import requests
import os
import subprocess
import shutil
import threading
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Configuration.

BASE_URL = "http://172.22.215.130:8080" 
DOSSIER_RACINE = "donnees_sequences"
PAYS = ["PT","CH","DE","GB","CZ","FR","DK","LV","RU","HR",
        "SI","GR","IT","RO","LT","SE","ES","BE","NO","FI",
        "PL","NL","BY","LU","UA","AL","IE","AT","EE","RS",
        "HU","ME","BG","SK","MD","IS"]

# Authentification
print("[TEST] VERIFICATION DU RESEAU...")
try:
    test = requests.get(BASE_URL, timeout=5)
    print(f"[OK] Serveur joignable (Code: {test.status_code})")
except Exception as e:
    print(f"[ERREUR] Impossible de joindre le serveur {BASE_URL}")
    print("Verifiez votre VPN ou connexion Univ.")
    sys.exit(1)

if not os.path.exists(DOSSIER_RACINE):
    os.makedirs(DOSSIER_RACINE)

verrou_git = threading.Lock()

def synchroniser_et_nettoyer(code_pays, dossier_pays):
    # C'est ici que ça envoie ET supprime
    with verrou_git:
        print(f"[GIT] Envoi des donnees pour {code_pays}...")
        try:
            # 1. Git Add & Commit & Push
            subprocess.run(["git", "add", dossier_pays], check=True)
            subprocess.run(["git", "commit", "-m", f"Data: {code_pays}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            # 2. Suppression (CONFIRMATION)
            print(f"[DELETE] Suppression IMMEDIATE du dossier {dossier_pays} du PC local.")
            shutil.rmtree(dossier_pays) # C'est cette commande qui efface tout
            print(f"[CLEAN] Espace disque libere pour {code_pays}.")
            
        except Exception as e:
            print(f"[ERREUR] Git a echoue pour {code_pays}: {e}")

def traiter_pays(code_pays):
    dossier_pays = os.path.join(DOSSIER_RACINE, code_pays)
    if not os.path.exists(dossier_pays):
        os.makedirs(dossier_pays)
        
    print(f"[START] Recherche pour {code_pays} (Depart 1978)...")
    fichiers_trouves = 0
    annee = 1978 
    
    # Boucle infinie MAIS avec securite
    while True:
        stop_pays = False
        
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            trimestre = f"{annee}{q}"
            url = f"{BASE_URL}/archived/sequences/{code_pays}/{trimestre}"
            nom_fichier = f"{code_pays}_{trimestre}.fasta"
            chemin_final = os.path.join(dossier_pays, nom_fichier)
            
            try:
                # On essaie de telecharger
                reponse = requests.get(url, timeout=3)
                
                # CAS 1 : C'est le futur (Texte explicite)
                if "Too early" in reponse.text:
                    print(f"   [STOP] Futur atteint pour {code_pays} a {trimestre}")
                    stop_pays = True
                    break
                
                # CAS 2 : Erreur 404 (Page inexistante) -> Stop aussi.
                if reponse.status_code == 404:
                    # Si on est apres 2020 et qu'on a une 404, on considere que c'est fini
                    if annee > 2020:
                        stop_pays = True
                        break
                    # Si c'est avant (ex: 1980), c'est peut-etre juste un trou dans les donnees, on continue
                
                # CAS 3 : Succes (200 OK)
                if reponse.status_code == 200:
                    with open(chemin_final, "wb") as f:
                        f.write(reponse.content)
                    print(f"   [OK] {code_pays} -> {trimestre} telecharge.")
                    fichiers_trouves += 1
            
            except Exception as e:
                print(f"   [RESEAU] Erreur sur {trimestre} : {e}")

        # Si on a recu l'ordre d'arreter (404 ou Too Early), on sort de la boucle WHILE
        if stop_pays:
            break
        
        # Securite ultime : si on depasse 2030, on force l'arret (evite le bug de l'an 2700)
        if annee > 2030:
            break

        annee += 1
    
    # Fin du pays : on synchronise SI on a trouve quelque chose
    if fichiers_trouves > 0:
        synchroniser_et_nettoyer(code_pays, dossier_pays)
    else:
        print(f"[INFO] {code_pays} : Aucune donnee trouvee (Dossier vide supprime).")
        try:
            os.rmdir(dossier_pays)
        except:
            pass

# Lancement
print(f" Demarrage START ({len(PAYS)} PAYS) ")
# On lance tout en parallele
with ThreadPoolExecutor(max_workers=len(PAYS)) as executor:
    executor.map(traiter_pays, PAYS)
print(" Termine : Vous etes ammené à consulter Github, lol...  ")
