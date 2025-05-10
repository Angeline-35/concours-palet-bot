import re
import os
import requests
import pandas as pd
import pytesseract
import cv2
import numpy as np
from datetime import datetime
from facebook_scraper import get_posts

PAGE_ID = "61554949372064"
CSV_PATH = "concours_palet.csv"


# 🔍 OCR depuis image URL
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


# 📌 Extraction date, heure, lieu
def extract_concours_info(text):
    infos = {}

    # Date (souple)
    date_match = re.search(r"(\d{1,2})\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-zé]*\s*(20\d{2})?", text, re.IGNORECASE)
    if date_match:
        mois_fr = {
            "janv": 1, "févr": 2, "mars": 3, "avr": 4, "mai": 5, "juin": 6,
            "juil": 7, "août": 8, "sept": 9, "oct": 10, "nov": 11, "déc": 12
        }
        jour = int(date_match.group(1))
        mois = mois_fr[date_match.group(2).lower()[:4]]
        annee = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
        infos["Date"] = datetime(annee, mois, jour).strftime("%Y-%m-%d")

    # Heure
    heure_match = re.search(r"\b(\d{1,2})[h:](\d{0,2})\b", text)
    if heure_match:
        h = heure_match.group(1)
        m = heure_match.group(2) if heure_match.group(2) else "00"
        infos["Heure"] = f"{h}:{m}"

    # Lieu
    lieu_match = re.search(r"(?:à\s+|lieu\s*[:\-]?\s*)([A-ZÉÈÀA-Za-z\s\-']{3,})", text, re.IGNORECASE)
    if lieu_match:
        infos["Lieu"] = lieu_match.group(1).strip()

    return infos if "Date" in infos else {}


# 🧪 Test OCR sur flyer exemple (image publique)
def test_flyer_ocr():
    flyer_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Tournoi.jpg/640px-Tournoi.jpg"
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


# 🔁 Traitement des publications Facebook
def process_facebook_posts(df):
    count = 0
    for post in get_posts(PAGE_ID, pages=3):
        text = post.get("text", "")
        infos = extract_concours_info(text)

        if not infos:
            images = post.get("images", [])
            for img_url in images:
                print(f"🖼️ Analyse OCR image : {img_url}")
                ocr_text = extract_text_from_image(img_url)
                infos = extract_concours_info(ocr_text)
                if infos:
                    break

        if infos and not ((df["Date"] == infos["Date"]) & (df["Heure"] == infos["Heure"])).any():
            df.loc[len(df)] = infos
            count += 1

    return df, count


def main():
    # Charger ou créer CSV
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=["Date", "Heure", "Lieu"])

    # OCR de test
    infos_flyer = test_flyer_ocr()
    if infos_flyer and not ((df["Date"] == infos_flyer["Date"]) & (df["Heure"] == infos_flyer["Heure"])).any():
        df.loc[len(df)] = infos_flyer

    # Facebook
    df, nb_nouveaux = process_facebook_posts(df)

    # Nettoyage et sauvegarde
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    df = df[df["Date"] >= aujourd_hui].sort_values(by="Date")
    df.to_csv(CSV_PATH, index=False)

    print(f"\n✅ {nb_nouveaux} concours à venir enregistrés dans : {CSV_PATH}")


if __name__ == "__main__":
    main()
