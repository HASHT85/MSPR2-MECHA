<p align="center">
  <h1 align="center">🏭 MECHA — Maintenance Predictive Industrielle</h1>
  <p align="center">
    <strong>Plateforme IA de maintenance prédictive pour un groupe industriel international</strong>
  </p>
  <p align="center">
    <a href="https://github.com/HASHT85/MSPR2-MECHA/actions/workflows/ci.yml">
      <img src="https://github.com/HASHT85/MSPR2-MECHA/actions/workflows/ci.yml/badge.svg" alt="CI/CD">
    </a>
    <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
    <img src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/Grafana-11.6-F46800?logo=grafana&logoColor=white" alt="Grafana">
    <img src="https://img.shields.io/badge/Streamlit-1.40-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</p>

---

## 📋 Contexte

**MECHA** est un groupe industriel opérant **5 usines** en France et en Espagne, avec **100 machines industrielles** à superviser. Ce projet implémente une solution complète de **maintenance prédictive** basée sur l'Intelligence Artificielle, permettant d'anticiper les pannes, optimiser la planification de maintenance et réduire les arrêts non planifiés.

> **MSPR 2 — Bloc 4 RNCP35584** | EPSI — Expert en Ingénierie Informatique

---

## 🏗️ Architecture

| Service | Technologie | Port | Description |
|---------|------------|------|-------------|
| **API** | FastAPI | `8000` | API REST de prédiction ML (9 endpoints) |
| **Dashboard** | Streamlit | `8501` | Dashboard métier multi-niveaux (5 vues), consomme l'API pour toutes les prédictions IA |
| **Monitoring** | Grafana | `3000` | Supervision temps réel (3 dashboards par rôle) |
| **Base de données** | PostgreSQL 15 | `5432` | Stockage des données capteurs (110k mesures) |

---

## 🖥️ Screenshots

### 📊 Dashboard Streamlit (Ajout MSPR 2 — Analyse IA)

#### Vue Site — Directeur d'Usine
<p align="center">
  <img src="docs/images/streamlit_site.png" alt="Streamlit Vue Site" width="800">
</p>

#### Vue Machine — Diagnostic Individuel
<p align="center">
  <img src="docs/images/streamlit_machine.png" alt="Streamlit Vue Machine" width="800">
</p>

#### Centre d'Alertes
<p align="center">
  <img src="docs/images/streamlit_alertes.png" alt="Streamlit Alertes" width="800">
</p>

#### Performance du Modèle IA
<p align="center">
  <img src="docs/images/streamlit_modele_ia.png" alt="Streamlit Modèle IA" width="800">
</p>

#### Tendance Température par Machine
<p align="center">
  <img src="docs/images/streamlit_temperature.png" alt="Streamlit Température" width="800">
</p>

### 📈 Grafana (Retenu MSPR 1 — Monitoring Temps Réel)

#### Direction Générale (DG Groupe)
<p align="center">
  <img src="docs/images/grafana_dg.png" alt="Grafana DG Groupe" width="800">
</p>

#### Directeur d'Usine
<p align="center">
  <img src="docs/images/grafana_usine.png" alt="Grafana Directeur Usine" width="800">
</p>

#### Technicien Maintenance
<p align="center">
  <img src="docs/images/grafana_technicien.png" alt="Grafana Technicien" width="800">
</p>

---

## 🤖 Modèles ML

| Modèle | Type | F1-Score | AUC-ROC | Usage |
|--------|------|----------|---------|-------|
| **Random Forest** | Classification | **80.4%** | 98.8% | Prédiction de pannes (modèle principal) |
| **XGBoost** | Classification | 81.1% | **98.8%** | Prédiction de pannes (alternatif) |
| **Logistic Regression** | Classification | 23.3% | 89.5% | Baseline de comparaison |
| **Isolation Forest** | Anomalie | — | 83.9% | Détection d'anomalies non-supervisée |
| **RF Regressor** | Régression | MAE=27 min | R²=0.72 | Estimation RUL (durée de vie restante, en minutes) |

> Métriques mesurées sur le jeu de test (22 000 lignes), lues par l'API sur `GET /metrics`.
> Sur la partie **réelle** (AI4I 2020) du jeu de test, le F1 tombe à ~7 % : les capteurs AI4I
> (couple, usure d'outil) ne sont pas dans les 10 features capteurs communes. Limite documentée et assumée.

### Bonnes pratiques ML
- ✅ **10 features capteurs uniquement** — `predicted_remaining_life` et `downtime_risk` sont **exclus** des entrées (ils contiennent la réponse : fuite de données corrigée), tout comme `machine_status`
- ✅ **Split temporel 80/20 par source de données** — on entraîne sur le passé, on teste sur le futur, et les données réelles AI4I sont présentes dans le train comme dans le test
- ✅ **Métriques ventilées par source** (simulé vs réel) pour ne pas masquer un modèle nul sur le réel
- ✅ **Gestion du déséquilibre** — `class_weight='balanced'` / `scale_pos_weight`
- ✅ **5 Model Cards** conformes EU AI Act

---

## 🚀 Démarrage rapide

### Prérequis
- [Docker](https://www.docker.com/) & Docker Compose
- [Git](https://git-scm.com/)

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/HASHT85/MSPR2-MECHA.git
cd MSPR2-MECHA

# 2. Configurer l'environnement
cp .env.example .env
# Editer .env pour définir POSTGRES_PASSWORD

# 3. Lancer l'application
docker compose up -d

# 4. Vérifier les services
docker compose ps
```

### Régénérer les données et les modèles (reproductibilité)

Les jeux de données finaux et les modèles `.joblib` ne sont pas versionnés (fichiers lourds).
Ils se reconstruisent de zéro en trois commandes, exactement comme le fait la CI :

```bash
python data/scripts/generate_data.py      # 100 000 lignes simulées -> data/raw + data/processed
python data/scripts/merge_datasets.py     # fusion avec AI4I 2020 (10 000 lignes réelles) -> 110 000 lignes
python models/training/train_models.py    # 5 modèles -> models/saved_models + métriques JSON (~10 s)
```

Sans modèles, l'API démarre en **mode fallback** (heuristiques) et le signale sur `GET /health`
(`models_loaded: false`). Le dashboard affiche alors « MODE MOCK » dans la barre latérale.

### Accès aux services

| Service | URL | Identifiants |
|---------|-----|-------------|
| **Dashboard** | [http://localhost:8501](http://localhost:8501) | — |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | API Key (si configurée) |
| **Grafana** | [http://localhost:3000](http://localhost:3000) | `admin` / voir `.env` |

---

## 📊 Dashboards par rôle

| Dashboard | Public cible | Contenu |
|-----------|-------------|---------|
| **DG Groupe** | Direction Générale | KPIs consolidés 5 usines, benchmark inter-sites |
| **Directeur Usine** | Directeur de site | Filtrable par usine, jauges capteurs, détail machines |
| **Technicien** | Équipe maintenance | Alertes, plan d'action prioritaire avec recommandations |

### Dashboard Streamlit (5 vues)
- **Groupe** — Vision consolidée du groupe industriel
- **Site** — Performance détaillée par usine
- **Machine** — Fiche individuelle avec historique capteurs
- **Alertes** — Système d'alertes avec niveaux de sévérité
- **Modèle IA** — Métriques ML et explicabilité

---

## 🔌 API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/predict` | Prédiction maintenance (1 machine) |
| `POST` | `/predict/batch` | Prédiction batch (jusqu'à 100 machines) |
| `POST` | `/predict/rul` | Estimation de durée de vie restante (RUL) |
| `POST` | `/anomaly` | Détection d'anomalies (Isolation Forest) |
| `GET` | `/metrics` | Métriques d'entraînement des modèles + statistiques API |
| `GET` | `/model-info` | Model cards résumées des modèles chargés |
| `GET` | `/alerts/config` | Configuration des seuils d'alerte |
| `PUT` | `/alerts/config` | Mise à jour des seuils d'alerte |

### Exemple de requête

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 85.5,
    "vibration": 45.2,
    "humidity": 60.0,
    "pressure": 2.5,
    "energy_consumption": 3.8,
    "machine_id": "12"
  }'
```

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest -v

# Avec couverture
pytest --cov=api --cov=models --cov-report=term-missing -v
```

**102 tests** couvrant :
- 🔬 Qualité des données (19 tests)
- 🔌 Intégration API (6 tests)
- 🤖 Modèles ML (16 tests, dont la cohérence entraînement ↔ API et le chargement réel des modèles par l'API)
- 📡 Endpoints API (61 tests)

En CI, les données et les modèles sont régénérés avant les tests : aucun test n'est sauté.

---

## 📁 Structure du projet

```
MSPR2-MECHA/
├── 📂 api/                    # API FastAPI
│   ├── main.py                # 9 endpoints REST
│   └── Dockerfile             # Image Docker multi-stage
├── 📂 app/src/                # Dashboard Streamlit
│   └── dashboard.py           # 5 vues métier (prédictions via l'API)
├── 📂 data/                   # Pipeline de données
│   ├── scripts/               # Génération + fusion datasets
│   ├── processed/             # Dataset final (110k lignes)
│   └── data_dictionary.md     # Dictionnaire de données
├── 📂 db/                     # Base de données
│   ├── init.sql               # Schéma PostgreSQL (4 tables, 9 index)
│   └── load_data.sh           # Ingestion automatique des données
├── 📂 docs/                   # Documentation (9 documents, 180+ KB)
├── 📂 grafana/                # Monitoring
│   ├── dashboards/            # 3 dashboards JSON par rôle
│   └── provisioning/          # Datasource + dashboard auto
├── 📂 models/                 # Machine Learning
│   ├── saved_models/          # 5 modèles entraînés (.joblib)
│   ├── model_cards/           # 5 fiches modèles (EU AI Act)
│   ├── evaluation/            # Métriques JSON
│   └── training/              # Script d'entraînement
├── 📂 tests/                  # Tests (102 tests)
├── 🐳 docker-compose.yml      # Orchestration 4 services
├── ⚙️ .env.example             # Configuration template
├── 🧹 ruff.toml                # Règles de lint/format (CI)
└── 📄 README.md               # Ce fichier
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | Architecture technique détaillée |
| [Choix techniques](docs/technical_choices.md) | Justification des technologies |
| [Plan de validation](docs/validation_plan.md) | Stratégie de test et recette |
| [Plan de déploiement](docs/deployment_plan.md) | Procédure de mise en production |
| [Conduite du changement](docs/change_management.md) | Accompagnement des utilisateurs |
| [Analyse RGPD](docs/rgpd_analysis.md) | Conformité RGPD et EU AI Act |
| [Interview client](docs/client_interview.md) | Entretien avec le client fictif |
| [Guide utilisateur](docs/user_guide.md) | Manuel d'utilisation |
| [Soutenance](docs/soutenance.md) | Support de présentation orale |

---

## 🔒 Sécurité

- Variables sensibles dans `.env` (jamais commitées)
- API Key optionnelle via header `X-API-Key`
- Volumes Docker en lecture seule (`:ro`) pour données et modèles
- Health checks sur tous les services
- Utilisateur non-root dans le container API
- Analyse RGPD et EU AI Act documentée

---

## 👥 Équipe

Projet réalisé dans le cadre de la **MSPR 2 — Bloc 4** (EPSI RNCP35584)

---

<p align="center">
  <sub>Built with ❤️ using Python, FastAPI, Streamlit, Grafana & Docker</sub>
</p>
