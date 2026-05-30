# 🏭 MECHA — Prototype IA de Maintenance Prédictive Industrielle

> **MSPR 2 — Bloc 4** | Certification RNCP35584 — EPSI  
> Équipe MECHA : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel

## 📋 Description

Prototype fonctionnel d'intelligence artificielle pour la **maintenance prédictive** des machines industrielles de MECHA, entreprise spécialisée dans la fabrication de pièces mécaniques de haute précision pour l'aéronautique et l'automobile.

Ce projet s'inscrit dans la **continuité directe de la MSPR 1** (cadrage & faisabilité) et passe à la phase de **conception et réalisation concrète**.

### Fonctionnalités principales

- 🔮 **Prédiction de maintenance** — Classification de l'état machine (normal / à risque)
- ⏱️ **Estimation RUL** — Prédiction du temps restant avant défaillance
- 🔍 **Détection d'anomalies** — Identification de comportements atypiques des capteurs
- 📊 **Dashboard métier** — Interface de pilotage pour les équipes maintenance et production
- 🚨 **Système d'alertes** — Notifications automatiques avec seuils configurables
- 🔌 **API REST** — Exposition des modèles IA via FastAPI

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Sources de Données                    │
│  Capteurs IoT │ SCADA/MES │ Dataset simulé/enrichi      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Couche Données (PostgreSQL)                  │
│  Ingestion → Nettoyage → Feature Engineering → Stockage  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Couche IA/ML                           │
│  Random Forest │ XGBoost │ Isolation Forest │ LR         │
│  Classification │ Régression RUL │ Détection anomalies   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│               Couche Applicative                         │
│  FastAPI (REST) │ Streamlit (Dashboard) │ Grafana        │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Python 3.11+ (pour le développement local)

### Lancement avec Docker

```bash
# Cloner le repo
git clone https://github.com/votre-repo/MSPR2-MECHA.git
cd MSPR2-MECHA

# Lancer tous les services
docker-compose up --build

# Accéder aux services :
# - API :       http://localhost:8000/docs
# - Dashboard : http://localhost:8501
# - Grafana :   http://localhost:3000
```

### Développement local

```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Générer les données enrichies
python data/scripts/generate_data.py

# Entraîner les modèles
python models/training/train_models.py

# Lancer l'API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Lancer le dashboard
streamlit run app/src/dashboard.py
```

## 📁 Structure du projet

```
MSPR2-MECHA/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .github/workflows/ci.yml
├── data/
│   ├── raw/                    # Données brutes
│   ├── processed/              # Données transformées
│   ├── data_dictionary.md      # Dictionnaire de données
│   └── scripts/                # Scripts génération/transformation
├── models/
│   ├── training/               # Scripts d'entraînement
│   ├── evaluation/             # Résultats et métriques
│   ├── model_cards/            # Documentation modèles (EU AI Act)
│   └── saved_models/           # Modèles sérialisés
├── api/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt
│   └── tests/                  # Tests unitaires
├── app/
│   ├── Dockerfile
│   └── src/                    # Dashboard Streamlit
├── docs/                       # Documentation complète
├── grafana/dashboards/         # Config Grafana
└── tests/                      # Tests globaux
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=api --cov=models --cov-report=html
```

## 📊 Modèles IA

| Modèle | Rôle | F1 (MSPR 1) | Objectif MSPR 2 |
|--------|------|-------------|-----------------|
| Random Forest | Classification maintenance | 71% | > 75% |
| XGBoost | Classification maintenance | — | > 75% |
| Régression Logistique | Baseline comparaison | 47% | Référence |
| Isolation Forest | Détection anomalies | 38% | Complémentaire |
| RF Regressor | Prédiction RUL | — | MAE < 50 min |

## 📜 Conformité

- **EU AI Act** : Human-in-the-Loop obligatoire, model cards pour chaque modèle
- **RGPD** : Données machine uniquement (pas de données personnelles)
- **NIS2** : Principes de cybersécurité respectés
- **IEC 62443** : Cloisonnement OT/IT documenté

## 👥 Équipe

| Membre | Rôle |
|--------|------|
| Malek El Fayedh | Data Science & ML |
| Thibaut Doreau | Architecture & DevOps |
| Vincent Gonçalves | Développement API & Tests |
| Pierre-Louis Guinel | Dashboard & Documentation |

## 📄 Licence

Projet pédagogique — EPSI — Certification RNCP35584
