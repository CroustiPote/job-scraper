# 🔍 Job Scraper — Veille emploi automatique

Script Python qui collecte automatiquement chaque matin les offres CDI/CDD sur **Indeed** et **LinkedIn**, filtre les résultats selon tes critères, et met à jour un CSV sur GitHub.

---

## 📋 Ce que fait ce projet

- 🔍 Scrape **Indeed**, **LinkedIn** et **Google Jobs** chaque matin
- 🚫 Exclut automatiquement les **stages et alternances** (et tout ce que tu configures)
- 🔁 **Déduplique** les offres déjà vues
- 💾 Stocke tout dans un **CSV** consultable dans Excel / Google Sheets
- 🌐 **Dashboard web** pour visualiser et gérer les offres
- ⏰ Tourne **automatiquement** via GitHub Actions (gratuit)

---

## 🌐 Accéder au dashboard

👉 **[Ouvrir le dashboard](https://croustipote.github.io/job-scraper/dashboard.html)**

## ⚙️ Configurer ton propre scraper

👉 **[Ouvrir le configurateur](https://croustipote.github.io/job-scraper/configurator.html)**

Remplis le formulaire en 3 minutes et télécharge ton script Python personnalisé — aucune connaissance technique requise.

---

## 🚀 Installation

### 1 — Installer Python 3.11

```bash
brew install python@3.11   # Mac
```

Ou télécharge sur [python.org](https://www.python.org/downloads/) (Windows).

### 2 — Installer les dépendances

```bash
python3.11 -m pip install python-jobspy requests beautifulsoup4 lxml feedparser
```

### 3 — Lancer le script

```bash
python3.11 job_scraper.py
```

Un fichier `offres_emploi.csv` est créé dans le dossier.

---

## ⚙️ Configuration

Dans `job_scraper.py`, section `CONFIG` :

```python
"keywords": [
    "motion designer",
    "graphiste",
    # Ajoute tes mots-clés ici
],

"exclude_keywords": [
    "stage", "alternance",
    # Ajoute les mots à exclure ici
],

"location": "Paris, France",
```

---

## ⏰ Automatisation (GitHub Actions)

Le workflow `.github/workflows/daily_scraper.yml` tourne automatiquement **du lundi au vendredi à 8h** et met à jour le CSV sur GitHub.

---

## 📊 Structure du CSV

| Colonne | Description |
|---------|-------------|
| `id` | Identifiant unique |
| `date_ajout` | Date de découverte |
| `titre` | Intitulé du poste |
| `entreprise` | Nom de l'entreprise |
| `lieu` | Ville |
| `contrat` | CDI / CDD |
| `source` | Indeed / Linkedin / Google |
| `lien` | Lien direct vers l'offre |
| `description_courte` | Extrait de la description |
