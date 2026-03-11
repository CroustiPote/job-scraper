"""
╔══════════════════════════════════════════════════════╗
║         🎨 JOB SCRAPER - Design & Motion Paris       ║
║  Indeed + LinkedIn + Welcome to the Jungle           ║
╚══════════════════════════════════════════════════════╝

Usage :
    python3.11 job_scraper.py           → lancement normal
    python3.11 job_scraper.py --debug   → test des sources

Dépendances :
    pip3 install python-jobspy requests beautifulsoup4 lxml feedparser
"""

import csv, os, smtplib, hashlib, sys, json, requests, feedparser
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ═══════════════════════════════════════════════════════

CONFIG = {
    "csv_file": "offres_emploi.csv",

    "keywords": [
        "motion designer",
        "graphiste",
        "directeur artistique",
        "graphic designer",
        "motion design",
        "infographiste",
        "after effects",
        "DA digital",
        "designer graphique",
        "visual designer",
        "brand designer",
        "identite visuelle",
        "illustrateur",
        "maquettiste",
        "art director",
        "designer print",
        "motion graphics",
        "animateur 2D",
    ],

    "exclude_keywords": [
        # Contrats non voulus
        "stage", "stagiaire", "alternance", "alternant",
        "apprentissage", "apprenti", "intern", "internship",
        # Commercial / Marketing
        "commercial", "commerciale", "commerciaux",
        "charge de marketing", "marketing manager", "chef de produit",
        "account manager", "business developer", "ingenieur commercial",
        "technico-commercial", "responsable marketing",
        # Tech / IT
        "developpeur", "programmeur", "ingenieur logiciel",
        "data analyst", "scrum master", "devops",
        # RH / Admin
        "recruteur", "charge rh", "comptable",
        "assistant administratif", "juriste", "office manager",
        # Hors scope creatif
        "photographe", "videaste", "cameraman",
        "monteur video", "realisateur", "chef operateur",
        # Regisseurs
        "regisseur", "regisseure", "regisseurs",
    ],

    "location": "Paris, France",

    "email": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender": "ton.email@gmail.com",
        "password": "ton_mot_de_passe_app",
        "recipient": "ton.email@gmail.com",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# ═══════════════════════════════════════════════════════
# 🔧 UTILITAIRES
# ═══════════════════════════════════════════════════════

def generate_id(title, company):
    raw = f"{title.lower().strip()}{company.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def load_existing_ids(csv_file):
    ids = set()
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ids.add(row.get("id", ""))
    return ids

def is_excluded(text):
    t = text.lower()
    return any(kw in t for kw in CONFIG["exclude_keywords"])

def save_jobs(jobs, csv_file):
    fieldnames = ["id", "date_ajout", "titre", "entreprise", "lieu",
                  "contrat", "source", "lien", "description_courte"]
    file_exists = os.path.exists(csv_file)
    with open(csv_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(jobs)
    print(f"  ✅ {len(jobs)} nouvelle(s) offre(s) sauvegardée(s)")

def make_job(id, titre, entreprise, lieu, contrat, source, lien, desc=""):
    return {
        "id": id,
        "date_ajout": date.today().isoformat(),
        "titre": titre,
        "entreprise": entreprise,
        "lieu": lieu,
        "contrat": contrat,
        "source": source,
        "lien": lien,
        "description_courte": desc[:200].replace("\n", " "),
    }

# ═══════════════════════════════════════════════════════
# 📡 SOURCE 1 — INDEED + LINKEDIN via python-jobspy
# ═══════════════════════════════════════════════════════

def scrape_jobspy(keyword, existing_ids):
    jobs = []
    try:
        from jobspy import scrape_jobs
        results = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=keyword,
            location="Paris, France",
            results_wanted=20,
            hours_old=72,
            country_indeed="France",
            linkedin_fetch_description=False,
            verbose=0,
        )
        if results is None or results.empty:
            return jobs

        for _, row in results.iterrows():
            title    = str(row.get("title", "") or "")
            company  = str(row.get("company", "") or "Inconnue")
            job_type = str(row.get("job_type", "") or "")
            desc     = str(row.get("description", "") or "")
            link     = str(row.get("job_url", "") or "")
            source   = str(row.get("site", "") or "").capitalize()

            if is_excluded(title + " " + job_type + " " + desc[:300]):
                continue

            job_id = generate_id(title, company)
            if job_id in existing_ids:
                continue
            existing_ids.add(job_id)

            jt = job_type.lower()
            contrat = ("CDI" if any(x in jt for x in ["full", "permanent"])
                       else "CDD" if any(x in jt for x in ["fixed", "contract", "cdd"])
                       else "CDI/CDD")

            jobs.append(make_job(job_id, title, company, "Paris", contrat, source, link, desc))

    except ImportError:
        print("  ⚠️  python-jobspy non installé — pip3 install python-jobspy")
    except Exception as e:
        print(f"  ⚠️  Erreur jobspy ({keyword}) : {e}")
    return jobs

# ═══════════════════════════════════════════════════════
# 📡 SOURCE 2 — WELCOME TO THE JUNGLE via RSS
# WTTJ expose un flux RSS public par recherche — fiable !
# ═══════════════════════════════════════════════════════

def scrape_wttj(keyword, existing_ids):
    jobs = []

    # WTTJ flux RSS public
    rss_url = (
        "https://www.welcometothejungle.com/fr/jobs.rss"
        f"?query={requests.utils.quote(keyword)}"
        "&aroundLatLng=48.8566%2C2.3522"
        "&aroundRadius=30"
        "&contractType[]=full_time"
        "&contractType[]=fixed_term"
    )

    try:
        r = requests.get(rss_url, headers=HEADERS, timeout=15)

        if r.status_code == 200 and "<rss" in r.text[:500].lower():
            feed = feedparser.parse(r.text)

            for entry in feed.entries:
                title   = entry.get("title", "").strip()
                link    = entry.get("link", "")
                summary = entry.get("summary", "")
                # WTTJ met "Entreprise - Lieu" dans le champ author ou tags
                company = "Inconnue"
                if hasattr(entry, "author"):
                    company = entry.author
                elif entry.get("tags"):
                    company = entry.tags[0].get("term", "Inconnue")

                if not title or is_excluded(title + " " + summary):
                    continue

                job_id = generate_id(title, company)
                if job_id in existing_ids:
                    continue
                existing_ids.add(job_id)

                desc = BeautifulSoup(summary, "html.parser").get_text()[:200]
                jobs.append(make_job(job_id, title, company, "Paris", "CDI/CDD", "WTTJ", link, desc))

        else:
            print(f"  ↩️  RSS WTTJ indisponible (HTTP {r.status_code}), tentative JSON...")
            jobs += scrape_wttj_json(keyword, existing_ids)

    except Exception as e:
        print(f"  ⚠️  Erreur WTTJ RSS ({keyword}) : {e}")
        jobs += scrape_wttj_json(keyword, existing_ids)

    sleep(1.5)
    return jobs


def scrape_wttj_json(keyword, existing_ids):
    """Fallback : cherche un bloc JSON dans les scripts de la page WTTJ."""
    jobs = []
    url = (
        "https://www.welcometothejungle.com/fr/jobs"
        f"?query={requests.utils.quote(keyword)}"
        "&aroundLatLng=48.8566%2C2.3522&aroundRadius=30"
        "&contractType[]=full_time&contractType[]=fixed_term"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            content = script.string or ""
            if '"name"' in content and '"organization"' in content and '"slug"' in content:
                try:
                    start = content.find("[{")
                    end   = content.rfind("}]") + 2
                    if start >= 0 and end > start:
                        items = json.loads(content[start:end])
                        for job in items[:20]:
                            title   = job.get("name", "")
                            org     = job.get("organization", {})
                            company = org.get("name", "Inconnue")
                            slug    = job.get("slug", "")
                            org_slug= org.get("slug", "")
                            link    = f"https://www.welcometothejungle.com/fr/companies/{org_slug}/jobs/{slug}"

                            if not title or is_excluded(title):
                                continue
                            job_id = generate_id(title, company)
                            if job_id in existing_ids:
                                continue
                            existing_ids.add(job_id)
                            jobs.append(make_job(job_id, title, company, "Paris", "CDI/CDD", "WTTJ", link))
                        if jobs:
                            return jobs
                except Exception:
                    continue
    except Exception as e:
        print(f"  ⚠️  Erreur WTTJ JSON fallback : {e}")
    return jobs

# ═══════════════════════════════════════════════════════
# 🔧 MODE DEBUG
# ═══════════════════════════════════════════════════════

def debug_sources():
    print("\n🔧 MODE DEBUG\n")
    kw = "motion designer"

    # Test jobspy
    try:
        from jobspy import scrape_jobs
        print("✅ python-jobspy installé")
        print("   Test Indeed/LinkedIn (10-15s)...")
        r = scrape_jobs(site_name=["indeed", "linkedin"], search_term=kw,
                        location="Paris, France", results_wanted=3,
                        country_indeed="France", verbose=0)
        nb = len(r) if r is not None else 0
        print(f"   → {nb} résultat(s)")
        if nb > 0:
            print(f"   Exemple : {r.iloc[0]['title']} @ {r.iloc[0]['company']}")
    except ImportError:
        print("❌ python-jobspy non installé")
    except Exception as e:
        print(f"⚠️  jobspy : {e}")

    print()

    # Test WTTJ RSS
    rss_url = (
        "https://www.welcometothejungle.com/fr/jobs.rss"
        f"?query={requests.utils.quote(kw)}"
        "&aroundLatLng=48.8566%2C2.3522&aroundRadius=30"
        "&contractType[]=full_time&contractType[]=fixed_term"
    )
    try:
        r = requests.get(rss_url, headers=HEADERS, timeout=15)
        is_rss = "<rss" in r.text[:500].lower()
        feed = feedparser.parse(r.text) if is_rss else None
        nb = len(feed.entries) if feed else 0
        print(f"WTTJ RSS → HTTP {r.status_code} | {'✅ RSS valide' if is_rss else '❌ pas de RSS'} | {nb} entrées")
        if nb > 0:
            print(f"   Exemple : {feed.entries[0].get('title', '?')}")
    except Exception as e:
        print(f"❌ WTTJ RSS → {e}")

# ═══════════════════════════════════════════════════════
# 📧 EMAIL
# ═══════════════════════════════════════════════════════

def send_email_recap(new_jobs):
    cfg = CONFIG["email"]
    if not cfg["enabled"] or not new_jobs:
        return
    today = datetime.now().strftime("%d/%m/%Y")
    rows = "".join(f"""<tr>
      <td style="padding:8px;border-bottom:1px solid #eee;">
        <a href="{j['lien']}" style="color:#6C47FF;font-weight:bold;text-decoration:none;">{j['titre']}</a>
        <br><small style="color:#666;">{j['entreprise']}</small>
      </td>
      <td style="padding:8px;border-bottom:1px solid #eee;">{j['contrat']}</td>
      <td style="padding:8px;border-bottom:1px solid #eee;color:#999;font-size:12px;">{j['source']}</td>
    </tr>""" for j in new_jobs)
    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px;">
      <div style="background:#6C47FF;color:white;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">🎨 Nouvelles offres Design & Motion</h2>
        <p style="margin:5px 0 0;">{today} — Paris</p>
      </div>
      <table style="width:100%;border-collapse:collapse;background:white;border:1px solid #eee;">
        <thead><tr style="background:#f5f5f5;">
          <th style="padding:10px;text-align:left;">Poste / Entreprise</th>
          <th style="padding:10px;text-align:left;">Contrat</th>
          <th style="padding:10px;text-align:left;">Source</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#999;font-size:12px;margin-top:15px;">Généré automatiquement — {len(new_jobs)} offres</p>
    </body></html>"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎨 {len(new_jobs)} nouvelles offres Design/Motion — {today}"
        msg["From"] = cfg["sender"]
        msg["To"] = cfg["recipient"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.send_message(msg)
        print(f"  📧 Email envoyé à {cfg['recipient']}")
    except Exception as e:
        print(f"  ⚠️  Erreur email : {e}")

# ═══════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════

def main():
    print("=" * 55)
    print("  🎨 JOB SCRAPER — Design & Motion Paris")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 55)

    existing_ids = load_existing_ids(CONFIG["csv_file"])
    print(f"\n📂 {len(existing_ids)} offres déjà en base\n")

    all_new_jobs = []

    for keyword in CONFIG["keywords"]:
        print(f"\n🔍 Recherche : « {keyword} »")

        print("  → Indeed + LinkedIn...")
        j = scrape_jobspy(keyword, existing_ids)
        print(f"     {len(j)} nouvelle(s) offre(s)")
        all_new_jobs.extend(j)



    print(f"\n💾 Sauvegarde...")
    if all_new_jobs:
        save_jobs(all_new_jobs, CONFIG["csv_file"])
    else:
        print("  Aucune nouvelle offre aujourd'hui.")

    if CONFIG["email"]["enabled"]:
        send_email_recap(all_new_jobs)

    total = len(load_existing_ids(CONFIG["csv_file"]))
    print(f"\n{'=' * 55}")
    print(f"  ✅ {len(all_new_jobs)} nouvelles offres ajoutées")
    print(f"  📊 Total en base : {total} offres")
    print(f"  📂 Fichier : {CONFIG['csv_file']}")
    print("=" * 55)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        debug_sources()
    else:
        main()
