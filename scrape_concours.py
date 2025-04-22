# scrape_concours.py

from facebook_scraper import get_posts
import pandas as pd
import re
import os
from datetime import datetime

def scraper_concours():
    group_id = "1509372826257136"
    pages = 10
    fichier_csv = "concours_palet.csv"

    heure_regex = r"\b(\d{1,2}h(?:\d{2})?)\b"
    lieu_regex = r"à\s+([A-ZÉÈÀa-zçêôâîùûéè'’\- ]+)"
    
    concours = []

    if os.path.exists(fichier_csv):
        df_ancien = pd.read_csv(fichier_csv)
        anciens_urls = set(df_ancien["Lien du post"])
    else:
        df_ancien = pd.DataFrame()
        anciens_urls = set()

    for post in get_posts(group=group_id, pages=pages):
        texte = post.get('text', '').lower()
        post_url = post.get('post_url')

        if post_url in anciens_urls:
            continue

        if "palet" in texte and ("concours" in texte or "tournoi" in texte):
            heure_trouvee = None
            lieu_trouve = None
            date_post = post.get("time")

            heures = re.findall(heure_regex, texte)
            if heures:
                heure_trouvee = heures[0]

            lieux = re.findall(lieu_regex, texte)
            if lieux:
                lieu_trouve = lieux[0]

            date_complete = date_post.strftime("%d/%m/%Y") if date_post else None

            concours.append({
                "Date": date_complete,
                "Heure": heure_trouvee,
                "Lieu": lieu_trouve,
                "Texte complet": post.get('text'),
                "Lien du post": post_url
            })

    if concours:
        df_nouveaux = pd.DataFrame(concours)
        df_total = pd.concat([df_ancien, df_nouveaux], ignore_index=True)
        df_total = df_total.drop_duplicates(subset=["Lien du post"])

        # Nettoyage : suppression concours passés
        df_total["Date"] = pd.to_datetime(df_total["Date"], format="%d/%m/%Y", errors='coerce')
        aujourdhui = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        df_total = df_total[df_total["Date"] >= aujourdhui]
        df_total = df_total.sort_values(by="Date")
        df_total["Date"] = df_total["Date"].dt.strftime("%d/%m/%Y")

        df_total.to_csv(fichier_csv, index=False, encoding='utf-8-sig')
        print(f"{len(df_nouveaux)} nouveau(x) concours ajouté(s).")
    else:
        print("Aucun nouveau concours trouvé.")

if __name__ == "__main__":
    scraper_concours()
