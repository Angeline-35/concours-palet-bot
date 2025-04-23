import pandas as pd
import pytesseract
from PIL import Image
from facebook_scraper import get_posts
from datetime import datetime
import re
import requests
from io import BytesIO
import os

# 🔧 Config
GROUP_ID = "1509372826257136"
CSV_FILE = "concours_palet.csv"
PAGES_TO_SCRAPE = 3

# 🧠 Expressions régulières pour extraire infos
date_pattern = r"(?:le\s*)?(\d{1,2}[\/\-\.\s]?(?:\d{1,2})?[\/\-\.\s]?\d{2,4})"
heure_pattern = r"(\d{1,2}h\d{0,2})"
lieu_pattern = r"(?:à|au|chez)\s+([A-ZÉÈÀA-Za-z\s\-']{3,})"

def extract_text_from_image_url(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        text = pytesseract.image_to_string(img, lang='fra')
        return text
    except Exception as e:
        print(f"[OCR] Erreur image : {e}")
        return ""

def extract_concours_info(text):
    infos = {}
    date_match = re.search(date_pattern, text, re.IGNORECASE)
    heure_match = re.search(heure_pattern, text)
    lieu_match = re.search(lieu_pattern, text, re.IGNORECASE)

    if date_match:
        try:
            raw_date = date_match.group(1).replace(" ", "/").replace(".", "/").replace("-", "/")
            parsed_date = datetime.strptime(raw_date, "%d/%m/%Y")
            infos["Date"] = parsed_date.strftime("%Y-%m-%d")
        except:
            try:
                parsed_date = datetime.strptime(raw_date, "%d/%m")
                infos["Date"] = parsed_date.replace(year=datetime.now().year).strftime("%Y-%m-%d")
            except:
                pass
    if heure_match:
        infos["Heure"] = heure_match.group(1).replace("h", ":")
    if lieu_match:
        infos["Lieu"] = lieu_match.group(1).strip()

    return infos if "Date" in infos else {}

# 📥 Charger les concours existants
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["Date", "Heure", "Lieu"])

# 🔄 Scraping des publications
nouveaux_concours = []

for post in get_posts(group=GROUP_ID, pages=PAGES_TO_SCRAPE, options={"comments": False}):
    full_text = post.get("text", "") or ""
    
    # 🔎 Ajout du texte OCR des images
    if post.get("images"):
        for url in post["images"]:
            full_text += "\n" + extract_text_from_image_url(url)
        print("="*60)
        print("TEXTE DU FLYER DÉTECTÉ :")
        print(full_text)
        print("="*60)

    infos = extract_concours_info(full_text)

    if infos and infos["Date"] >= datetime.now().strftime("%Y-%m-%d"):
        if not (
            ((df["Date"] == infos.get("Date")) & (df["Lieu"] == infos.get("Lieu"))).any()
        ):
            nouveaux_concours.append(infos)

# ➕ Fusionner et nettoyer
if nouveaux_concours:
    df = pd.concat([df, pd.DataFrame(nouveaux_concours)], ignore_index=True)

# 🧹 Supprimer les concours passés
aujourdhui = datetime.now().strftime("%Y-%m-%d")
df = df[df["Date"] >= aujourdhui]

# 📅 Trier par date
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
df = df.sort_values("Date").reset_index(drop=True)
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

# 💾 Enregistrer
df.to_csv(CSV_FILE, index=False)

# TEST 
test_text = "Concours de palet – samedi 27 avril 2024 à 14h à Plélan-le-Grand"
infos = extract_concours_info(test_text)
print("Infos détectées :", infos)

print(f"{len(nouveaux_concours)} nouveaux concours ajoutés.")
