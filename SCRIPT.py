



import requests
import os
import subprocess
import shutil

# --- CONFIGURATION ---
BASE_URL = "http://172.22.215.130:8080"
DOSSIER_CIBLE = "premiere_sequence"

# Liste des pays
PAYS = ["PT","CH","DE","GB","CZ","FR","DK","LV","RU","HR",
        "SI","GR","IT","RO","LT","SE","ES","BE","NO","FI",
        "PL","NL","BY","LU","UA","AL","IE","AT","EE","RS",
        "HU","ME","BG","SK","MD","IS"]

# Création du dossier s'il n'existe pas
if not os.path.exists(DOSSIER_CIBLE):
    os.makedirs(DOSSIER_CIBLE)

# --- FONCTION : SYNCHRONISATION ET SUPPRESSION ---
def synchroniser_et_nettoyer(code_pays):
    print(f" [GIT] Synchronisation pour le pays : {code_pays}...")
    try:
        # 1. Ajouter tout
        subprocess.run(["git", "add", "."], check=True)
        
        # 2. Commit
        subprocess.run(["git", "commit", "-m", f"Ajout data : {code_pays}"], check=True)
        
        # 3. Push
        resultat_push = subprocess.run(["git", "push", "origin", "main"], check=True)
        
        # 4. Suppression locale (Uniquement si le push est OK)
        if resultat_push.returncode == 0:
            print(f" [CLEAN] Suppression fichiers locaux pour {code_pays}...")
            for fichier in os.listdir(DOSSIER_CIBLE):
                chemin_fichier = os.path.join(DOSSIER_CIBLE, fichier)
                if os.path.isfile(chemin_fichier):
                    os.remove(chemin_fichier)
                    
    except subprocess.CalledProcessError as e:
        print(f" [ERREUR] Problème avec Git : {e}")

# --- MOTEUR PRINCIPAL ---
print("--- DÉMARRAGE DU PIPELINE (LOGIQUE INFINIE) ---")

for pays in PAYS:
    print(f">> Traitement du pays : {pays}")
    fichiers_telecharges = 0
    
    # DÉBUT LOGIQUE PURE : On commence en 1987
    annee = 1987
    
    # On boucle à l'infini, seul le serveur peut nous arrêter
    while True:
        arret_pays = False
        
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            trimestre = f"{annee}{q}"
            
            url = f"{BASE_URL}/archived/sequences/{pays}/{trimestre}"
            nom_fichier = f"{pays}_{trimestre}.fasta"
            chemin_sauvegarde = os.path.join(DOSSIER_CIBLE, nom_fichier)
            
            try:
                # Requête GET
                reponse = requests.get(url, timeout=5)
                
                # LA SEULE CONDITION D'ARRÊT : "Too early"
                if "Too early" in reponse.text:
                    print(f"   [STOP] Futur atteint pour {pays} à {trimestre}")
                    arret_pays = True
                    break
                
                # Si succès (Code 200)
                if reponse.status_code == 200:
                    with open(chemin_sauvegarde, "wb") as f:
                        f.write(reponse.content)
                    fichiers_telecharges += 1
                    
            except Exception:
                pass # On ignore les erreurs techniques
        
        # Si on a touché le futur, on sort de la boucle "while" pour changer de pays
        if arret_pays:
            break
        
        # Sinon, on passe à l'année suivante
        annee += 1
            
    # Fin du pays : on push et on vide le disque
    if fichiers_telecharges > 0:
        synchroniser_et_nettoyer(pays)

print("--- TERMINÉ : TOUT EST SUR GITHUB ---")
