# 🏗️ Architecture Technique — MECHA Predict

> **Projet** : MECHA — Maintenance Prédictive par Intelligence Artificielle  
> **Version** : 1.0  
> **Date** : 30/05/2026  
> **Auteurs** : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel  
> **Compétence couverte** : **C2 — Concevoir une architecture applicative**

---

## 1. Introduction

Ce document présente l'architecture technique de la solution **MECHA Predict**, une plateforme de maintenance prédictive basée sur l'intelligence artificielle destinée aux 5 usines du groupe MECHA. L'objectif est de passer d'une maintenance curative coûteuse à une maintenance prédictive optimisée, en exploitant les données des capteurs IoT installés sur les 50 machines de production.

### 1.1 Objectifs de l'architecture

| Objectif | Description |
|----------|-------------|
| **Collecte temps réel** | Ingérer les données de 50 machines (température, vibration, pression, humidité, courant) |
| **Stockage structuré** | Centraliser les données dans une base relationnelle performante |
| **Prédiction IA** | Détecter les anomalies et prédire les pannes avant qu'elles ne surviennent |
| **Visualisation** | Fournir des tableaux de bord adaptés à chaque profil utilisateur |
| **Déploiement** | Assurer un déploiement reproductible et scalable via conteneurisation |
| **Automatisation** | Intégrer un pipeline CI/CD pour garantir la qualité du code |

---

## 2. Vue d'ensemble de l'architecture

L'architecture suit un modèle **en couches** (layered architecture) permettant une séparation claire des responsabilités :

1. **Couche Acquisition** — Capteurs IoT → Broker MQTT
2. **Couche Ingestion** — Scripts Python de collecte et transformation
3. **Couche Stockage** — PostgreSQL (données brutes + prédictions)
4. **Couche Intelligence** — Pipeline ML (prétraitement, entraînement, inférence)
5. **Couche Service** — API REST FastAPI
6. **Couche Présentation** — Streamlit (équipe data) + Grafana (opérateurs)
7. **Couche Transverse** — Docker (conteneurisation) + GitHub Actions (CI/CD)

### 2.1 Diagramme d'architecture globale

```mermaid
graph TB
    subgraph "🏭 Usines MECHA (5 sites)"
        subgraph "Capteurs IoT (50 machines)"
            S1["🌡️ Température"]
            S2["📳 Vibration"]
            S3["⚙️ Pression"]
            S4["💧 Humidité"]
            S5["⚡ Courant"]
        end
    end

    subgraph "📡 Couche Acquisition"
        MQTT["MQTT Broker<br/>(Mosquitto)"]
    end

    subgraph "🔄 Couche Ingestion"
        COLLECT["Script de collecte<br/>(Python + paho-mqtt)"]
        ETL["Pipeline ELT<br/>(nettoyage, validation)"]
    end

    subgraph "💾 Couche Stockage"
        PG["PostgreSQL 16<br/>(données brutes +<br/>prédictions + alertes)"]
    end

    subgraph "🧠 Couche Intelligence"
        PREPROC["Prétraitement<br/>(feature engineering)"]
        RF["Random Forest<br/>(classification pannes)"]
        XGB["XGBoost<br/>(estimation RUL)"]
        TRAIN["Pipeline d'entraînement<br/>(scikit-learn)"]
    end

    subgraph "🌐 Couche Service"
        API["FastAPI<br/>(API REST)"]
        EP1["/predict"]
        EP2["/health"]
        EP3["/machines"]
        EP4["/alerts"]
    end

    subgraph "📊 Couche Présentation"
        STREAM["Streamlit<br/>(équipe data/direction)"]
        GRAF["Grafana<br/>(opérateurs/maintenance)"]
    end

    subgraph "🔧 Couche Transverse"
        DOCKER["Docker / Docker Compose"]
        GHACTIONS["GitHub Actions<br/>(CI/CD)"]
    end

    S1 & S2 & S3 & S4 & S5 --> MQTT
    MQTT --> COLLECT
    COLLECT --> ETL
    ETL --> PG
    PG --> PREPROC
    PREPROC --> RF & XGB
    RF & XGB --> TRAIN
    TRAIN --> PG
    PG --> API
    API --> EP1 & EP2 & EP3 & EP4
    API --> STREAM
    API --> GRAF
    DOCKER -.-> API & STREAM & GRAF & PG
    GHACTIONS -.-> DOCKER
```

---

## 3. Description détaillée des couches

### 3.1 Couche Acquisition — Capteurs IoT & MQTT

**Rôle** : Collecter les données brutes des capteurs en temps réel.

| Élément | Détail |
|---------|--------|
| **Capteurs** | 50 machines × 5 types de capteurs = ~250 flux de données |
| **Protocole** | MQTT (Message Queuing Telemetry Transport) |
| **Broker** | Eclipse Mosquitto (léger, open-source, éprouvé en industrie) |
| **Fréquence** | 1 mesure / seconde par capteur (configurable) |
| **Format** | JSON (`{"machine_id": "LYN-CNC-01", "sensor": "temperature", "value": 72.3, "timestamp": "..."}`) |

**Justification MQTT** : Protocole standard IoT, faible bande passante, fiable même en connectivité dégradée (QoS configurable), nativement pub/sub.

### 3.2 Couche Ingestion — Pipeline ELT

**Rôle** : Transformer et charger les données brutes dans la base.

L'approche **ELT** (Extract-Load-Transform) est privilégiée sur ETL car :
- Les données sont d'abord chargées brutes dans PostgreSQL (traçabilité)
- Les transformations sont appliquées en SQL ou Python en aval
- Permet de conserver les données originales pour audit

| Étape | Outil | Description |
|-------|-------|-------------|
| Extract | paho-mqtt (Python) | Souscription aux topics MQTT |
| Load | psycopg2 / SQLAlchemy | Insertion en base PostgreSQL |
| Transform | pandas / SQL | Nettoyage, validation, feature engineering |

### 3.3 Couche Stockage — PostgreSQL

**Rôle** : Stocker l'ensemble des données de manière structurée et requêtable.

**Justification PostgreSQL** :
- Base relationnelle mature et robuste (30+ ans d'existence)
- Support natif JSON pour les données semi-structurées des capteurs
- Extensible (TimescaleDB pour les séries temporelles si besoin)
- Open-source, sans coût de licence
- Excellentes performances en lecture/écriture
- Conformité ACID pour la fiabilité des transactions

#### Modèle de données

```mermaid
erDiagram
    USINES {
        int id PK
        varchar nom
        varchar ville
        varchar pays
        varchar fuseau_horaire
    }
    
    MACHINES {
        int id PK
        varchar code_machine
        varchar type_machine
        varchar modele
        date date_mise_service
        int usine_id FK
        varchar statut
    }
    
    CAPTEURS {
        int id PK
        varchar type_capteur
        varchar unite_mesure
        float seuil_min
        float seuil_max
        int machine_id FK
    }
    
    MESURES {
        bigint id PK
        int capteur_id FK
        timestamp horodatage
        float valeur
        boolean est_anomalie
    }
    
    PREDICTIONS {
        int id PK
        int machine_id FK
        timestamp date_prediction
        varchar type_prediction
        float score_confiance
        float rul_heures
        varchar modele_utilise
    }
    
    ALERTES {
        int id PK
        int prediction_id FK
        int machine_id FK
        varchar niveau
        varchar message
        timestamp date_creation
        timestamp date_acquittement
        varchar statut
    }
    
    MAINTENANCES {
        int id PK
        int machine_id FK
        int alerte_id FK
        varchar type_maintenance
        timestamp date_planifiee
        timestamp date_realisee
        text description
        varchar statut
    }

    USINES ||--o{ MACHINES : "contient"
    MACHINES ||--o{ CAPTEURS : "équipée de"
    CAPTEURS ||--o{ MESURES : "produit"
    MACHINES ||--o{ PREDICTIONS : "concerne"
    PREDICTIONS ||--o{ ALERTES : "génère"
    MACHINES ||--o{ ALERTES : "concerne"
    MACHINES ||--o{ MAINTENANCES : "subit"
    ALERTES ||--o| MAINTENANCES : "déclenche"
```

### 3.4 Couche Intelligence — Pipeline ML

**Rôle** : Entraîner les modèles et générer des prédictions.

#### Pipeline de traitement

```mermaid
graph LR
    A["Données brutes<br/>(mesures capteurs)"] --> B["Nettoyage<br/>(valeurs aberrantes,<br/>données manquantes)"]
    B --> C["Feature Engineering<br/>(moyennes glissantes,<br/>écarts-types, tendances)"]
    C --> D["Sélection features<br/>(importance, corrélation)"]
    D --> E{"Entraînement"}
    E --> F["Random Forest<br/>(classification panne)"]
    E --> G["XGBoost<br/>(estimation RUL)"]
    F --> H["Évaluation<br/>(accuracy, F1, recall)"]
    G --> H
    H --> I["Sérialisation<br/>(joblib / pickle)"]
    I --> J["Modèle en production"]
```

| Modèle | Rôle | Métriques cibles |
|--------|------|------------------|
| **Random Forest** | Classification binaire (panne imminente oui/non) | Recall ≥ 90%, Precision ≥ 85% |
| **XGBoost** | Régression (estimation RUL en heures) | MAE ≤ 24h, R² ≥ 0.85 |

**Features extraites** :
- Moyennes glissantes (1h, 6h, 24h)
- Écarts-types glissants
- Dérivées (tendance à la hausse/baisse)
- Compteurs de dépassements de seuils
- Ratios inter-capteurs

### 3.5 Couche Service — API FastAPI

**Rôle** : Exposer les fonctionnalités via une API REST.

**Justification FastAPI** :
- Performance élevée (asynchrone, basé sur Starlette/Uvicorn)
- Documentation automatique (Swagger/OpenAPI)
- Validation native des données (Pydantic)
- Typage Python natif
- Idéal pour le prototypage rapide et la production

#### Endpoints principaux

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/health` | GET | État de santé de l'API | — |
| `/predict/{machine_id}` | POST | Lancer une prédiction pour une machine | `machine_id`, données capteurs |
| `/machines` | GET | Liste des machines et leur état | `usine_id` (optionnel) |
| `/machines/{id}` | GET | Détail d'une machine | `id` |
| `/alerts` | GET | Liste des alertes actives | `niveau`, `usine_id` (filtres) |
| `/alerts/{id}/acknowledge` | PUT | Acquitter une alerte | `id` |
| `/predictions/history` | GET | Historique des prédictions | `machine_id`, `date_debut`, `date_fin` |
| `/models/status` | GET | État des modèles ML déployés | — |

### 3.6 Couche Présentation — Streamlit & Grafana

#### Streamlit (équipe data / direction)

**Rôle** : Dashboard analytique pour l'exploration des données et le suivi des modèles.

| Fonctionnalité | Description |
|----------------|-------------|
| Vue d'ensemble | KPIs globaux, taux de disponibilité par usine |
| Analyse machine | Historique capteurs, tendances, prédictions |
| Performance modèles | Métriques ML, drift detection |
| Gestion alertes | Tableau des alertes avec filtres et actions |

**Justification Streamlit** : Prototypage rapide en Python pur, parfait pour l'équipe data, interactif, déployable facilement.

#### Grafana (opérateurs / maintenance)

**Rôle** : Monitoring temps réel pour les équipes terrain.

| Fonctionnalité | Description |
|----------------|-------------|
| Dashboards usine | Vue temps réel par site (1 dashboard / usine) |
| Courbes capteurs | Température, vibration, pression en temps réel |
| Alerting natif | Notifications (email, Slack) sur dépassement seuils |
| Historique | Exploration des données passées |

**Justification Grafana** : Standard industriel pour le monitoring, connexion native PostgreSQL, alerting intégré, familier des équipes ops.

### 3.7 Couche Transverse — Docker & CI/CD

#### Docker

Chaque composant est conteneurisé pour garantir la reproductibilité :

| Service | Image | Port |
|---------|-------|------|
| `api` | Python 3.11 + FastAPI | 8000 |
| `streamlit` | Python 3.11 + Streamlit | 8501 |
| `postgres` | PostgreSQL 16 | 5432 |
| `grafana` | Grafana OSS | 3000 |
| `mosquitto` | Eclipse Mosquitto | 1883 |
| `ml-worker` | Python 3.11 + scikit-learn | — |

**Justification Docker** :
- Isolation des services
- Déploiement identique dev/staging/prod
- Scalabilité horizontale possible
- Portabilité entre sites

#### GitHub Actions (CI/CD)

```mermaid
graph LR
    A["Push / PR"] --> B["Lint<br/>(flake8, black)"]
    B --> C["Tests unitaires<br/>(pytest)"]
    C --> D["Tests intégration<br/>(Docker Compose)"]
    D --> E["Build images<br/>Docker"]
    E --> F{"Branche ?"}
    F -->|main| G["Deploy staging"]
    F -->|release| H["Deploy production"]
    G --> I["Tests smoke"]
    I --> J["✅ Prêt"]
```

**Justification GitHub Actions** :
- Intégré nativement à GitHub (hébergement du code)
- Gratuit pour les projets open-source
- Configuration YAML simple
- Large écosystème d'actions réutilisables
- Secrets management intégré

---

## 4. Comparatif des choix techniques

### 4.1 Base de données

| Critère | PostgreSQL ✅ | MongoDB | InfluxDB |
|---------|:------------:|:-------:|:--------:|
| Maturité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| SQL standard | ✅ | ❌ | Partiel (InfluxQL) |
| Séries temporelles | ✅ (TimescaleDB) | ⚠️ | ✅ |
| Relations complexes | ✅ | ❌ | ❌ |
| Support JSON | ✅ (JSONB) | ✅ (natif) | ❌ |
| Coût | Gratuit | Gratuit (Community) | Gratuit (OSS) |
| Écosystème | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 4.2 Framework API

| Critère | FastAPI ✅ | Flask | Django REST |
|---------|:---------:|:-----:|:-----------:|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Doc automatique | ✅ (Swagger) | ❌ (manuel) | ✅ (DRF) |
| Asynchrone | ✅ (natif) | ⚠️ (via extension) | ⚠️ |
| Typage / Validation | ✅ (Pydantic) | ❌ | ✅ (Serializers) |
| Courbe d'apprentissage | Faible | Très faible | Moyenne |
| Taille projet | Léger | Léger | Lourd |

### 4.3 Dashboard

| Critère | Streamlit ✅ | Dash | Metabase |
|---------|:-----------:|:----:|:--------:|
| Langage | Python | Python | No-code |
| Prototypage rapide | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Interactivité | ✅ | ✅ | ⚠️ (limité) |
| Personnalisation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Déploiement | Simple | Moyen | Simple |
| Communauté | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

### 4.4 Conteneurisation

| Critère | Docker ✅ | VM | Bare Metal |
|---------|:--------:|:--:|:----------:|
| Isolation | ✅ | ✅ | ❌ |
| Légèreté | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Portabilité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| Reproductibilité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| Temps démarrage | Secondes | Minutes | — |
| Coût opérationnel | Faible | Élevé | Moyen |

### 4.5 CI/CD

| Critère | GitHub Actions ✅ | Jenkins | GitLab CI |
|---------|:----------------:|:-------:|:---------:|
| Intégration Git | ✅ (natif GitHub) | Via plugin | ✅ (natif GitLab) |
| Configuration | YAML (simple) | Groovy (complexe) | YAML |
| Maintenance | Aucune (SaaS) | Serveur dédié | Aucune (SaaS) |
| Coût | Gratuit (public) | Gratuit + infra | Gratuit (limité) |
| Écosystème | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 5. Diagramme de séquence — Flux de prédiction

```mermaid
sequenceDiagram
    participant C as Capteur IoT
    participant M as MQTT Broker
    participant I as Script Ingestion
    participant DB as PostgreSQL
    participant ML as Pipeline ML
    participant API as FastAPI
    participant UI as Streamlit/Grafana

    C->>M: Publie données capteur (JSON)
    M->>I: Délivre message (subscribe)
    I->>I: Validation & nettoyage
    I->>DB: INSERT mesures brutes
    
    Note over ML: Exécution périodique (cron)
    ML->>DB: SELECT dernières mesures
    ML->>ML: Feature engineering
    ML->>ML: Inférence (Random Forest + XGBoost)
    ML->>DB: INSERT prédictions + alertes

    UI->>API: GET /machines (tableau de bord)
    API->>DB: SELECT machines + statuts
    DB-->>API: Résultats
    API-->>UI: JSON (machines + alertes)

    UI->>API: GET /alerts (alertes actives)
    API->>DB: SELECT alertes WHERE statut='active'
    DB-->>API: Résultats
    API-->>UI: JSON (alertes)
```

---

## 6. Contraintes et prérequis techniques

### 6.1 Infrastructure réseau

| Prérequis | Détail |
|-----------|--------|
| Connectivité capteurs | Réseau local industriel (Ethernet/Wi-Fi industriel) |
| Bande passante | ≥ 10 Mbps par site (données capteurs + dashboards) |
| Latence | < 500ms capteur → broker MQTT |
| VPN inter-sites | Tunnel sécurisé entre les 5 usines et le serveur central |
| Ports ouverts | 1883 (MQTT), 5432 (PostgreSQL), 8000 (API), 8501 (Streamlit), 3000 (Grafana) |

### 6.2 Serveurs

| Composant | CPU | RAM | Stockage | OS |
|-----------|-----|-----|----------|-----|
| Serveur central (API + ML) | 8 vCPU | 32 Go | 500 Go SSD | Ubuntu 22.04 LTS |
| Serveur BDD | 4 vCPU | 16 Go | 1 To SSD | Ubuntu 22.04 LTS |
| Edge Gateway (par site) | 2 vCPU | 4 Go | 64 Go | Linux embarqué |

---

## 7. Évolutivité et scalabilité

### 7.1 Axes d'évolution

```mermaid
graph TD
    A["Architecture actuelle<br/>(monolithique conteneurisée)"] --> B["Court terme"]
    A --> C["Moyen terme"]
    A --> D["Long terme"]
    
    B --> B1["TimescaleDB<br/>(extension PostgreSQL<br/>pour séries temporelles)"]
    B --> B2["Redis<br/>(cache prédictions)"]
    
    C --> C1["Kubernetes<br/>(orchestration multi-sites)"]
    C --> C2["Apache Kafka<br/>(remplacement MQTT<br/>pour le streaming)"]
    
    D --> D1["Deep Learning<br/>(LSTM si données suffisantes)"]
    D --> D2["MLflow<br/>(versioning modèles)"]
    D --> D3["Data Lake<br/>(stockage brut massif)"]
```

### 7.2 Dimensionnement prévisionnel

| Métrique | Phase pilote (Lyon) | Déploiement complet (5 sites) |
|----------|:-------------------:|:-----------------------------:|
| Machines monitorées | 10 | 50 |
| Mesures / jour | ~864 000 | ~4 320 000 |
| Volume BDD / mois | ~2 Go | ~10 Go |
| Prédictions / jour | ~240 | ~1 200 |
| Utilisateurs simultanés | 5-10 | 30-50 |

---

## 8. Synthèse

L'architecture proposée répond aux exigences du projet MECHA en offrant :

- ✅ **Collecte fiable** des données IoT via MQTT
- ✅ **Stockage structuré** dans PostgreSQL avec un modèle de données adapté
- ✅ **Prédictions pertinentes** grâce aux modèles Random Forest et XGBoost
- ✅ **API moderne** avec FastAPI pour l'interopérabilité
- ✅ **Visualisation adaptée** avec Streamlit (data) et Grafana (terrain)
- ✅ **Déploiement reproductible** via Docker et Docker Compose
- ✅ **Qualité continue** grâce à GitHub Actions

Cette architecture modulaire permet une **évolution progressive** du système sans remise en cause de l'existant, accompagnant ainsi la montée en maturité du programme de maintenance prédictive de MECHA.

---

> **Document validé par** : Équipe projet MECHA  
> **Prochaine révision** : À l'issue de la phase pilote (Lyon)
