# Guide de Lancement Local & Scénario de Démo Live — Soutenance MSPR TPRE841

Ce guide explique comment récupérer et lancer toute la solution **MECHA Predict** sur votre propre PC portable avant d'entrer en salle de soutenance, avec un **mode principal Docker complet** et un **Plan B instantané sans Docker** (au cas où Docker Desktop ou le Wi-Fi de l'école poserait problème le jour J).

---

## 1. Préparation sur votre PC (à faire une seule fois la veille)

Ouvrez un terminal (**PowerShell** sur Windows, ou **Terminal** sur macOS/Linux) dans votre dossier de travail :

```bash
git clone https://github.com/HASHT85/MSPR2-MECHA.git
cd MSPR2-MECHA
```

*(Si le dépôt est déjà cloné sur votre PC : faites simplement `git checkout main && git pull --prune`.)*

### Premier lancement de chauffe (« Warm-up »)
Lancez le script une première fois chez vous avec une bonne connexion :
- **Sur Windows** : double-cliquez sur `start_demo.bat` (ou exécutez `.\start_demo.bat` dans PowerShell).
- **Sur macOS / Linux** : exécutez `./start_demo.sh`.

Ce premier lancement réalise automatiquement tout le travail lourd (~2 à 3 minutes la toute première fois) :
1. Création automatique du fichier `.env` depuis `.env.example`.
2. Génération du dataset hybride de **110 000 lignes** (`data/processed/mecha_dataset_processed.csv`).
3. Entraînement et sauvegarde des **5 modèles ML** (`models/saved_models/*.joblib`).
4. Construction des images Docker et chargement des 110 000 lignes dans **PostgreSQL 15**.

> **Astuce Jour J** : Une fois ce premier lancement fait la veille, les fichiers CSV, les 5 modèles `.joblib`, les images Docker et la base SQL restent en cache sur votre disque. Le jour de la soutenance, `start_demo.bat` (ou `./start_demo.sh`) démarre en **moins de 10 secondes** et fonctionne **100 % hors-ligne** (aucun besoin d'Internet !).

---

## 2. Lancement le Jour J (10 min avant d'entrer en salle)

### Option A — Mode Complet Docker (Recommandé : 4 services actifs)
Assurez-vous que **Docker Desktop** est ouvert, puis :
- **Windows** : double-clic sur `start_demo.bat`
- **macOS / Linux** : `./start_demo.sh`

Vos 3 onglets de démonstration s'ouvrent tout seuls dans le navigateur :
1. **Application Métier Streamlit (6 vues)** — port `8501`
2. **Documentation Interactive API IA (Swagger `/docs`)** — port `8000` (`/docs`)
3. **Supervision Temps Réel Grafana (3 dashboards)** — port `3000` (identifiants : `admin` / `changeme`)

### Option B — Plan B Secours Sans Docker (Python direct en 5 secondes)
Si Docker Desktop refuse de démarrer sur le PC de présentation :
- **Windows** : `.\start_demo.bat --local` *(note : si Docker Desktop est fermé, double-cliquer sur `start_demo.bat` bascule automatiquement sur ce mode !)*
- **macOS / Linux** : `./start_demo.sh --local`

Ce mode lance directement **FastAPI** (port `8000`) + **Streamlit 6 vues** (port `8501`) via un environnement Python local `.venv` et ouvre automatiquement les 2 onglets dans votre navigateur.

### Arrêt propre après la soutenance
- **Windows** : double-clic sur `stop_demo.bat`
- **macOS / Linux** : `./stop_demo.sh`

---

## 3. Chorégraphie de Démo Live en Soutenance (2 min 30 chrono)

Pour ne pas dépasser les **20 minutes** réglementaires (4 x 5 min), gardez les 3 onglets déjà ouverts avant de commencer et déroulez ce parcours fluide pendant le passage de **Vincent Gonçalves** (C4) et **Pierre-Louis Guinel** (C7/C8) :

1. **Swagger FastAPI (`/docs`, 30 s — compétence C4)** :
   - Montrer `GET /health` (`models_loaded: true`, 4 modèles chargés en mémoire).
   - Ouvrir `POST /predict` -> **Try it out** -> envoyer une mesure critique (`temperature: 96`, `vibration: 68`, `temp_rolling_10min: 94`, `vibr_rolling_10min: 65`) -> montrer la réponse JSON instantanée (< 50 ms) avec `probability`, `rul_minutes`, `is_anomaly` et `explanation.top_factors`.
2. **Dashboard Streamlit — Vue `Groupe` puis `Machine` (45 s — compétences C3 & C4)** :
   - Montrer la vue **Groupe** consolidée des **5 usines FR/ES** (Lyon, Toulouse, Nantes, Barcelone, Madrid).
   - Cliquer sur **Machine**, sélectionner une machine dégradée -> montrer les courbes capteurs, la probabilité IA de panne et le **RUL en minutes**.
3. **Dashboard Streamlit — Nouvelle 6e vue `Accompagnement` (45 s — compétences C8 & C4)** :
   - Onglet **Qualification Terrain (Human-in-the-Loop)** : enregistrer en direct une qualification anonyme (*Intervention planifiée — Vrai positif*) pour prouver la conformité **EU AI Act Art. 14** et **RGPD**.
   - Onglet **Paramétrage Seuils API (C4)** : montrer que le responsable maintenance peut ajuster le seuil de décision IA à chaud sans toucher au code.
4. **Grafana (30 s — compétence C2/Monitoring)** :
   - Basculer sur l'onglet Grafana -> ouvrir le dashboard **MECHA — Technicien Maintenance** connecté en temps réel à la vue SQL `v_machine_status` de PostgreSQL 15.
