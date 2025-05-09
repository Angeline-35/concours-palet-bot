import re
import os
import requests
import pandas as pd
import pytesseract
import cv2
import numpy as np
from datetime import datetime
from PIL import Image
from facebook_scraper import get_posts

PAGE_ID = "61554949372064"


# 🔍 Extraire le texte depuis une image via URL (OCR)
def extract_text_from_image(url):
    try:
        response = requests.get(url, stream=True)
        img_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        text = pytesseract.image_to_string(img, lang='fra')
        return text
    except Exception as e:
        print("Erreur OCR :", e)
        return ""

# 📌 Extraction d'infos depuis un texte (publication ou OCR)
def extract_concours_info(text):
    infos = {}

    date_match = re.search(r"(\d{1,2})\s*(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*(20\d{2})", text, re.IGNORECASE)
    if date_match:
        mois_fr = {
            "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
            "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
        }
        jour = int(date_match.group(1))
        mois = mois_fr[date_match.group(2).lower()]
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

# 📂 Chargement du fichier CSV s'il existe
csv_path = "concours_palet.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    df = pd.DataFrame(columns=["Date", "Heure", "Lieu"])


###
# 👇 Test OCR manuel sur un flyer
def test_flyer_ocr():
    flyer_url = "https://scontent.xx.fbcdn.net/v/t39.30808-6/441181134_2019829378544809_7314485221197299128_n.jpg"
    print("\n🧪 Test OCR sur flyer d'exemple...\n")
    ocr_text = extract_text_from_image(flyer_url)
    print("🧠 Texte OCR détecté :\n", ocr_text)
    infos = extract_concours_info(ocr_text)
    if infos:
        print("✅ Infos détectées :", infos)
        return infos
    else:
        print("❌ Aucune info détectée.")
        return {}

# Lancer le test OCR flyer avant tout le reste
infos_flyer = test_flyer_ocr()
if infos_flyer:
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["Date", "Heure", "Lieu"])

    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    if not ((df["Date"] == infos_flyer["Date"]) & (df["Heure"] == infos_flyer["Heure"])).any():
        df = pd.concat([df, pd.DataFrame([infos_flyer])], ignore_index=True)
        df = df[df["Date"] >= aujourd_hui]
        df = df.sort_values(by="Date")
        df.to_csv(csv_path, index=False)
        print("💾 Fichier mis à jour avec le flyer.")
###


# 🔁 Récupération des publications du groupe Facebook
for post in get_posts(PAGE_ID, pages=3):
    text = post.get("text", "")
    infos = extract_concours_info(text)

    # 📸 Si rien dans le texte, essayer OCR sur les images
    if not infos:
        images = post.get("images", [])
        for img_url in images:
            print(f"Analyse OCR image : {img_url}")
            ocr_text = extract_text_from_image(img_url)
            infos = extract_concours_info(ocr_text)
            if infos:
                break

    # 🆕 Ajouter si non déjà présent
    if infos and not ((df["Date"] == infos["Date"]) & (df["Heure"] == infos["Heure"])).any():
        print("✅ Nouveau concours détecté :", infos)
        df = pd.concat([df, pd.DataFrame([infos])], ignore_index=True)

#  Afficher le nombre de posts détectés
posts = list(get_posts(PAGE_ID, pages=1))
print(f"🔍 {len(posts)} publication(s) trouvée(s) dans le groupe.")


# 🧹 Supprimer les concours passés
aujourd_hui = datetime.now().strftime("%Y-%m-%d")
df = df[df["Date"] >= aujourd_hui]

# 📊 Trier par date croissante
df = df.sort_values(by="Date")
df.to_csv(csv_path, index=False)
print("✅ Fichier mis à jour :", csv_path)
