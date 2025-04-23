import re
from datetime import datetime
import pandas as pd

# Fonction d'extraction
def extract_concours_info(text):
    infos = {}

    date_match = re.search(r"(\d{1,2})\s*(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*(20\d{2})", text, re.IGNORECASE)
    if date_match:
        jours = {
            "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
            "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
        }
        jour = int(date_match.group(1))
        mois = jours[date_match.group(2).lower()]
        annee = int(date_match.group(3))
        infos["Date"] = datetime(annee, mois, jour).strftime("%Y-%m-%d")

    heure_match = re.search(r"(\d{1,2})h(\d{0,2})", text)
    if heure_match:
        h = heure_match.group(1)
        m = heure_match.group(2) if heure_match.group(2) else "00"
        infos["Heure"] = f"{h}:{m}"

    lieu_match = re.search(r"(?:à|lieu\s*[:\-]?)\s*([A-ZÉÈÀA-Za-z\s\-']{3,})", text, re.IGNORECASE)
    if lieu_match:
        infos["Lieu"] = lieu_match.group(1).strip()

    return infos if "Date" in infos else {}

# Test manuel
test_text = """
Concours de palet – samedi 27 avril 2024 à 14h
Lieu : Salle polyvalente de Plélan-le-Grand
"""

print("Test détection concours :")
infos = extract_concours_info(test_text)
print(infos)

# Sauvegarde dans le fichier CSV si les infos sont valides
if infos:
    df = pd.DataFrame([infos])
    df.to_csv("concours_palet.csv", index=False)
    print("Écrit dans concours_palet.csv")
else:
    print("Aucune info détectée – rien à écrire.")
