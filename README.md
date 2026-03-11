# 🎨 Job Scraper — Design & Motion Paris

Script Python qui collecte automatiquement chaque matin les offres CDI/CDD en **Graphic Design** et **Motion Design** sur Paris, depuis **Indeed** et **Welcome to the Jungle**.

---

## 📋 Ce que fait ce script

- 🔍 Cherche sur **Indeed** (via flux RSS) et **Welcome to the Jungle**
- 🚫 Exclut automatiquement les **stages et alternances**
- 🔁 **Déduplique** les offres déjà vues
- 💾 Stocke tout dans un fichier **CSV** consultable dans Excel/Google Sheets
- 📧 Peut envoyer un **email récap** chaque matin (optionnel)
- ⏰ Tourne **automatiquement chaque matin** via GitHub Actions (gratuit)

---

## 🚀 Installation en 4 étapes

### Étape 1 — Installer Python

Télécharge et installe Python depuis [python.org](https://www.python.org/downloads/)  
✅ Coche bien **"Add Python to PATH"** pendant l'installation.

Vérifie l'installation en ouvrant un terminal :
```bash
python --version
# Doit afficher : Python 3.11.x
```

---

### Étape 2 — Installer les dépendances

Dans le dossier du projet, ouvre un terminal et exécute :
```bash
pip install -r requirements.txt
```

---

### Étape 3 — Premier lancement (test local)

```bash
python job_scraper.py
```

Le script va créer un fichier `offres_emploi.csv` dans le même dossier.  
Tu peux l'ouvrir directement dans **Excel** ou **Google Sheets**.

---

### Étape 4 — Automatisation via GitHub (tourne tous les matins)

#### 4a. Créer un compte GitHub
Inscris-toi sur [github.com](https://github.com) (gratuit).

#### 4b. Créer un nouveau dépôt
1. Clique sur **"New repository"**
2. Nomme-le `job-scraper`
3. Coche **"Private"** (pour garder tes données privées)
4. Clique **"Create repository"**

#### 4c. Uploader les fichiers
Depuis ton terminal, dans le dossier du projet :
```bash
git init
git add .
git commit -m "🚀 Initial commit"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/job-scraper.git
git push -u origin main
```

#### 4d. Activer GitHub Actions
1. Va dans ton repo GitHub → onglet **"Actions"**
2. Le workflow `daily_scraper.yml` sera détecté automatiquement
3. Clique **"Enable"**
4. Pour tester : clique **"Run workflow"** manuellement

➡️ **C'est tout !** Le script tournera désormais chaque matin à 8h.

---

## 📧 Activer les emails récap (optionnel)

### Avec Gmail :
1. Active la **vérification en 2 étapes** sur ton compte Google
2. Va dans **Sécurité → Mots de passe des applications**
3. Crée un mot de passe pour "Job Scraper"

### Dans `job_scraper.py`, modifie :
```python
"email": {
    "enabled": True,              # ← Changer False en True
    "sender": "ton.email@gmail.com",
    "password": "xxxx xxxx xxxx xxxx",  # ← Mot de passe d'application
    "recipient": "ton.email@gmail.com",
}
```

### Pour GitHub Actions, ajoute des Secrets :
1. Repo GitHub → **Settings → Secrets → Actions**
2. Ajoute :
   - `EMAIL_SENDER` = ton email
   - `EMAIL_PASSWORD` = mot de passe d'application
   - `EMAIL_RECIPIENT` = où recevoir les récaps

---

## 🔧 Personnalisation

### Ajouter/supprimer des mots-clés
Dans `job_scraper.py`, section `CONFIG` :
```python
"keywords": [
    "motion designer",
    "graphiste",
    "directeur artistique",
    # Ajoute tes propres mots-clés ici
    "brand designer",
    "ui designer",
],
```

### Ajouter des mots à exclure
```python
"exclude_keywords": [
    "stage", "alternance",
    # Ajoute ici des mots pour filtrer des offres non pertinentes
    "junior",  # Si tu ne veux pas les postes junior
],
```

---

## 📊 Structure du CSV

| Colonne | Description |
|---------|-------------|
| `id` | Identifiant unique de l'offre |
| `date_ajout` | Date de découverte |
| `titre` | Intitulé du poste |
| `entreprise` | Nom de l'entreprise |
| `lieu` | Ville |
| `contrat` | CDI / CDD |
| `source` | Indeed / WTTJ |
| `lien` | Lien direct vers l'offre |
| `description_courte` | Extrait de la description |

---

## ❓ Problèmes fréquents

**"Module not found"** → Relance `pip install -r requirements.txt`

**Le CSV est vide** → Indeed et WTTJ peuvent bloquer temporairement les requêtes. Réessaie plus tard.

**GitHub Actions ne tourne pas** → Vérifie que le repo est bien public ou que GitHub Actions est activé dans les Settings.

---

## 📬 Aller plus loin

Une fois à l'aise, tu peux :
- Ajouter **Airtable** comme base de données (plus visuel qu'un CSV)
- Intégrer **LinkedIn Jobs** (nécessite une session authentifiée)
- Ajouter **Apec** ou **Cadremploi**
- Créer un mini **dashboard web** pour visualiser les offres
