# 🚀 Plan de Déploiement Multi-Sites — MECHA Predict

> **Projet** : MECHA — Maintenance Prédictive par Intelligence Artificielle  
> **Version** : 1.0  
> **Date** : 30/05/2026  
> **Auteurs** : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel  
> **Compétences couvertes** : **C3 — Développer une application** / **C4 — Solution intégrée**

---

## 1. Introduction et objectifs

### 1.1 Objectif du document

Ce document définit la stratégie de déploiement de la solution MECHA Predict sur les **5 sites industriels** du groupe MECHA. Il couvre les aspects techniques, organisationnels et opérationnels nécessaires à un déploiement progressif et maîtrisé.

### 1.2 Sites concernés

| Site | Ville | Pays | Machines | Spécialité | Priorité |
|------|-------|------|:--------:|-----------|:--------:|
| MECHA Lyon | Lyon | France 🇫🇷 | 12 | Aéro + Auto (siège) | 1 — Pilote |
| MECHA Toulouse | Toulouse | France 🇫🇷 | 10 | Aéronautique | 2 |
| MECHA Nantes | Nantes | France 🇫🇷 | 10 | Aéronautique | 3 |
| MECHA Barcelone | Barcelone | Espagne 🇪🇸 | 9 | Automobile | 4 |
| MECHA Madrid | Madrid | Espagne 🇪🇸 | 9 | Automobile | 5 |

### 1.3 Objectifs du déploiement

| Objectif | Indicateur | Cible |
|----------|-----------|:-----:|
| Couverture complète | Machines monitorées | 50/50 (100%) |
| Adoption utilisateur | Taux de connexion hebdo | ≥ 90% |
| Réduction arrêts | Arrêts non planifiés / mois | -50% vs baseline |
| Délai total | Durée du déploiement complet | ≤ 12 mois |

---

## 2. Prérequis techniques par site

### 2.1 Infrastructure réseau

| Prérequis | Spécification minimale | Lyon ✅ | Toulouse ⚠️ | Nantes ⚠️ | Barcelone ❓ | Madrid ❓ |
|-----------|----------------------|:------:|:---------:|:-------:|:----------:|:-------:|
| Réseau Ethernet industriel | ≥ 100 Mbps | ✅ | ✅ | En cours | À vérifier | À vérifier |
| Wi-Fi industriel | 802.11ac (backup) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Accès Internet sortant | ≥ 10 Mbps | ✅ | ✅ | ✅ | ✅ | ✅ |
| VPN inter-sites | IPsec ou WireGuard | ✅ | ✅ | ✅ | À configurer | À configurer |
| Firewall configuré | Ports ouverts (voir ci-dessous) | ✅ | ✅ | ⚠️ | ❓ | ❓ |

### 2.2 Ports réseau requis

| Port | Service | Direction | Usage |
|:----:|---------|-----------|-------|
| 1883 | MQTT (Mosquitto) | Capteurs → Broker | Données capteurs |
| 8883 | MQTTS (chiffré) | Capteurs → Broker | Données capteurs (prod) |
| 5432 | PostgreSQL | API → BDD | Requêtes base de données |
| 8000 | FastAPI | Dashboard → API | Requêtes REST |
| 8501 | Streamlit | Navigateur → Dashboard | Interface utilisateur |
| 3000 | Grafana | Navigateur → Monitoring | Monitoring temps réel |
| 443 | HTTPS | Tout → Reverse proxy | Accès sécurisé externe |

### 2.3 Serveurs requis

| Composant | Rôle | CPU | RAM | Stockage | Quantité |
|-----------|------|:---:|:---:|:--------:|:--------:|
| **Serveur central** | API + ML + Orchestration | 8 vCPU | 32 Go | 500 Go SSD | 1 (Lyon) |
| **Serveur BDD** | PostgreSQL | 4 vCPU | 16 Go | 1 To SSD | 1 (Lyon) |
| **Edge Gateway** | Collecte locale par site | 2 vCPU | 4 Go | 64 Go | 5 (1/site) |

### 2.4 Capteurs IoT compatibles

| Type de capteur | Protocole | Fréquence | Marques compatibles |
|----------------|-----------|-----------|-------------------|
| Température | MQTT / Modbus → MQTT gateway | 1 mesure/s | Siemens, Schneider, IFM |
| Vibration | MQTT / Modbus → MQTT gateway | 1 mesure/s | SKF, Fluke, IFM |
| Pression | MQTT / Modbus → MQTT gateway | 1 mesure/s | Endress+Hauser, WIKA |
| Courant | MQTT / Modbus → MQTT gateway | 1 mesure/s | Schneider, ABB |
| Humidité | MQTT | 1 mesure/min | Vaisala, Testo |

---

## 3. Architecture de déploiement

### 3.1 Architecture multi-sites

```mermaid
graph TB
    subgraph "🏢 Serveur Central (Lyon)"
        API["FastAPI<br/>(API REST)"]
        ML["Pipeline ML<br/>(scikit-learn)"]
        DB["PostgreSQL<br/>(base centralisée)"]
        STREAM["Streamlit<br/>(dashboard)"]
        GRAF["Grafana<br/>(monitoring)"]
        
        API --> DB
        ML --> DB
        STREAM --> API
        GRAF --> DB
    end
    
    subgraph "🏭 Lyon"
        GW1["Edge Gateway"]
        C1["Capteurs<br/>(12 machines)"]
        C1 --> GW1
    end
    
    subgraph "🏭 Toulouse"
        GW2["Edge Gateway"]
        C2["Capteurs<br/>(10 machines)"]
        C2 --> GW2
    end
    
    subgraph "🏭 Nantes"
        GW3["Edge Gateway"]
        C3["Capteurs<br/>(10 machines)"]
        C3 --> GW3
    end
    
    subgraph "🏭 Barcelone"
        GW4["Edge Gateway"]
        C4["Capteurs<br/>(9 machines)"]
        C4 --> GW4
    end
    
    subgraph "🏭 Madrid"
        GW5["Edge Gateway"]
        C5["Capteurs<br/>(9 machines)"]
        C5 --> GW5
    end
    
    GW1 -->|VPN| API
    GW2 -->|VPN| API
    GW3 -->|VPN| API
    GW4 -->|VPN| API
    GW5 -->|VPN| API
```

### 3.2 Choix : Centralisation

| Critère | Centralisé ✅ | Distribué |
|---------|:------------:|:---------:|
| Coût infrastructure | Faible (1 serveur central) | Élevé (serveur par site) |
| Cohérence des données | Garantie | Risque de désynchronisation |
| Maintenance | Simplifiée | Complexe (5 systèmes) |
| Entraînement ML | Toutes les données en un point | Agrégation nécessaire |
| Latence | Légèrement plus élevée | Très faible |
| Résilience | Point unique de défaillance | Haute disponibilité |

**Justification** : Avec 50 machines et ~4M mesures/jour, le volume reste gérable par un serveur centralisé. Les Edge Gateways assurent un buffer local en cas de perte de connectivité.

### 3.3 Stratégie de réplication BDD

La base PostgreSQL est centralisée à Lyon avec :
- **Backup quotidien** automatique (pg_dump + stockage distant)
- **Réplication streaming** vers un serveur standby (optionnel phase 4)
- **Buffer local** sur chaque Edge Gateway (SQLite) en cas de perte réseau

---

## 4. Stratégie de déploiement progressif

### 4.1 Planning global

```mermaid
gantt
    title Déploiement MECHA Predict — Multi-sites
    dateFormat  YYYY-MM-DD
    
    section Phase 1 : Pilote Lyon
    Audit infrastructure Lyon         :p1a, 2026-06-01, 7d
    Installation capteurs (10 machines):p1b, 2026-06-08, 14d
    Déploiement serveur central       :p1c, 2026-06-08, 7d
    Configuration Docker              :p1d, 2026-06-15, 7d
    Calibration modèles ML            :p1e, 2026-06-22, 21d
    Tests et validation               :p1f, 2026-07-13, 14d
    Mise en production pilote         :milestone, p1g, 2026-07-27, 0d
    Période d'observation (1 mois)    :p1h, 2026-07-28, 30d
    Go/No-Go Phase 2                  :milestone, p1i, 2026-08-31, 0d
    
    section Phase 2 : Toulouse + Nantes
    Audit infrastructure              :p2a, 2026-09-01, 7d
    Installation capteurs Toulouse    :p2b, 2026-09-08, 14d
    Installation capteurs Nantes      :p2c, 2026-09-08, 14d
    Configuration Edge Gateways       :p2d, 2026-09-22, 7d
    Calibration modèles ML            :p2e, 2026-09-29, 14d
    Tests et validation               :p2f, 2026-10-13, 14d
    Mise en production                :milestone, p2g, 2026-10-27, 0d
    Période d'observation             :p2h, 2026-10-28, 30d
    Go/No-Go Phase 3                  :milestone, p2i, 2026-11-30, 0d
    
    section Phase 3 : Barcelone + Madrid
    Adaptation linguistique           :p3a, 2026-12-01, 14d
    Audit infrastructure ES           :p3b, 2026-12-01, 7d
    Installation capteurs Barcelone   :p3c, 2026-12-15, 14d
    Installation capteurs Madrid      :p3d, 2026-12-15, 14d
    Configuration Edge Gateways       :p3e, 2026-12-29, 7d
    Calibration modèles ML            :p3f, 2027-01-05, 14d
    Tests et validation               :p3g, 2027-01-19, 14d
    Mise en production                :milestone, p3h, 2027-02-02, 0d
    
    section Phase 4 : Stabilisation
    Optimisation performance          :p4a, 2027-02-03, 30d
    Ajustement modèles ML             :p4b, 2027-02-03, 30d
    Formation continue                :p4c, 2027-02-03, 60d
    Bilan global                      :milestone, p4d, 2027-05-31, 0d
```

### 4.2 Phase 1 — Site pilote Lyon (10 machines)

#### Étapes détaillées

| N° | Étape | Durée | Responsable | Détail |
|----|-------|:-----:|-------------|--------|
| 1.1 | Audit infrastructure | 1 sem | Thibaut Doreau | Vérifier réseau, alimentation électrique, emplacement capteurs |
| 1.2 | Installation capteurs | 2 sem | Prestataire + Mme Martin | 5 capteurs/machine × 10 machines = 50 capteurs |
| 1.3 | Déploiement serveur central | 1 sem | Vincent Gonçalves | Installation Docker, configuration réseau |
| 1.4 | Configuration Docker Compose | 1 sem | Vincent Gonçalves | Tous les services (API, BDD, Streamlit, Grafana, MQTT) |
| 1.5 | Ingestion données test | 1 sem | Thibaut Doreau | Vérifier le flux capteurs → BDD |
| 1.6 | Calibration modèles ML | 3 sem | Pierre-Louis Guinel | Collecte 2-3 semaines de données, entraînement, validation |
| 1.7 | Configuration dashboards | 1 sem | Malek El Fayedh | Streamlit + Grafana personnalisés pour Lyon |
| 1.8 | Tests et validation | 2 sem | Équipe complète | Cf. plan de validation |
| 1.9 | Formation équipe Lyon | 1 sem | Pierre-Louis Guinel | Sessions formation maintenance |
| 1.10 | Mise en production | — | Équipe complète | Go live sur 10 machines |

#### Critères de succès du pilote

| Critère | Seuil minimum | Mesuré comment |
|---------|:------------:|---------------|
| Données capteurs reçues | ≥ 95% du temps | Monitoring Grafana |
| Précision des prédictions | ≥ 80% (accuracy) | Comparaison prédictions vs réalité |
| Taux de fausses alertes | ≤ 15% | Retours terrain |
| Adoption par l'équipe | ≥ 70% connexion hebdo | Logs applicatifs |
| Satisfaction utilisateur | ≥ 6/10 | Enquête |

### 4.3 Phase 2 — Sites France (Toulouse + Nantes)

| Spécificité | Détail |
|-------------|--------|
| **Réplication** | Configuration identique à Lyon (Docker Compose) |
| **Adaptation** | Calibration ML avec les données spécifiques de chaque site |
| **Capteurs** | Installation complète (sites peu équipés) |
| **Réseau** | Configuration VPN vers serveur central Lyon |
| **Formation** | Sessions sur site, basées sur le REX de Lyon |

### 4.4 Phase 3 — Sites Espagne (Barcelone + Madrid)

| Spécificité | Détail |
|-------------|--------|
| **Langue** | Interface Streamlit et Grafana en espagnol (i18n) |
| **Alertes** | Templates de notification en espagnol |
| **Documentation** | Guide utilisateur traduit en espagnol |
| **Formation** | Sessions en espagnol par un formateur local |
| **Réglementaire** | Conformité LOPDGDD (équivalent espagnol du RGPD) |
| **Support** | Ambassadeurs bilingues FR/ES |

---

## 5. Paramétrage et règles métiers

### 5.1 Seuils d'alerte par type de machine

| Type de machine | Capteur | Seuil normal | Seuil warning 🟡 | Seuil critique 🔴 |
|----------------|---------|:------------:|:----------------:|:-----------------:|
| CNC (usinage) | Température | < 75°C | 75-90°C | > 90°C |
| CNC (usinage) | Vibration | < 0.5 mm/s | 0.5-1.5 mm/s | > 1.5 mm/s |
| CNC (usinage) | Pression | 5-7 bar | 4-5 ou 7-8 bar | < 4 ou > 8 bar |
| Tour | Température | < 70°C | 70-85°C | > 85°C |
| Tour | Vibration | < 0.4 mm/s | 0.4-1.2 mm/s | > 1.2 mm/s |
| Rectifieuse | Température | < 65°C | 65-80°C | > 80°C |
| Rectifieuse | Vibration | < 0.3 mm/s | 0.3-1.0 mm/s | > 1.0 mm/s |

> ⚠️ Ces seuils sont des valeurs initiales qui seront affinés lors de la phase pilote en collaboration avec l'équipe maintenance.

### 5.2 Règles de notification

| Niveau | Délai max notification | Canaux | Destinataires |
|--------|:---------------------:|--------|-------------|
| **Information** 🔵 | 1 heure | Dashboard uniquement | Responsable maintenance |
| **Warning** 🟡 | 15 minutes | Email + Dashboard | Responsable maintenance + Technicien |
| **Critique** 🔴 | 5 minutes | SMS + Email + Dashboard | Responsable maintenance + Chef d'équipe + Direction |

### 5.3 Paramétrage des modèles par site

| Paramètre | Description | Personnalisation |
|-----------|-------------|-----------------|
| **Historique d'entraînement** | Données utilisées pour entraîner le modèle | Spécifique à chaque site (types de machines différents) |
| **Fréquence de ré-entraînement** | Périodicité de mise à jour du modèle | Mensuelle (automatique via cron) |
| **Seuil de confiance minimum** | En dessous, la prédiction n'est pas affichée | 60% (paramétrable par site) |
| **Fenêtre de prédiction** | Horizon temporel de la prédiction | 7 jours (ajustable) |

### 5.4 Configuration Grafana par usine

Chaque usine dispose de dashboards personnalisés :

| Dashboard | Contenu | Mise à jour |
|-----------|---------|:-----------:|
| **Vue d'ensemble usine** | Toutes les machines, codes couleur, KPIs | Temps réel |
| **Détail machine** | Historique capteurs, prédictions, alertes | Temps réel |
| **Performance maintenance** | MTBF, MTTR, taux de disponibilité | Horaire |
| **Alertes actives** | Liste et suivi des alertes en cours | Temps réel |

---

## 6. Procédure de déploiement technique

### 6.1 Docker Compose — Production

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  # --- Base de données ---
  postgres:
    image: postgres:16-alpine
    container_name: mecha-db
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # --- Broker MQTT ---
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mecha-mqtt
    restart: always
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - mosquitto_data:/mosquitto/data
    ports:
      - "1883:1883"
      - "8883:8883"

  # --- API FastAPI ---
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: mecha-api
    restart: always
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      MODEL_PATH: /app/models/current_model.joblib
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - models_data:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # --- Dashboard Streamlit ---
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: mecha-dashboard
    restart: always
    environment:
      API_URL: http://api:8000
      STREAMLIT_SERVER_PORT: 8501
    depends_on:
      - api
    ports:
      - "8501:8501"

  # --- Monitoring Grafana ---
  grafana:
    image: grafana/grafana:latest
    container_name: mecha-grafana
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-clock-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3000:3000"

  # --- Worker ML (entraînement + inférence) ---
  ml-worker:
    build:
      context: .
      dockerfile: Dockerfile.ml
    container_name: mecha-ml
    restart: always
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      MODEL_OUTPUT_PATH: /app/models
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - models_data:/app/models

volumes:
  postgres_data:
  mosquitto_data:
  grafana_data:
  models_data:
```

### 6.2 Variables d'environnement

```bash
# .env.production
DB_NAME=mecha_predict
DB_USER=mecha_admin
DB_PASSWORD=<mot_de_passe_fort>
SECRET_KEY=<clé_secrète_api>
GRAFANA_PASSWORD=<mot_de_passe_grafana>
MQTT_BROKER=mosquitto
MQTT_PORT=1883
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 6.3 Procédure de déploiement pas à pas

| Étape | Commande / Action | Vérification |
|:-----:|-------------------|-------------|
| 1 | `git clone` du repository sur le serveur | Code présent |
| 2 | Copier `.env.production` et renseigner les secrets | Variables définies |
| 3 | `docker compose -f docker-compose.prod.yml build` | Build sans erreur |
| 4 | `docker compose -f docker-compose.prod.yml up -d` | Tous les containers UP |
| 5 | Vérifier les health checks : `docker compose ps` | Tous « healthy » |
| 6 | Exécuter les migrations BDD | Tables créées |
| 7 | Importer les données de configuration (machines, capteurs) | Données en base |
| 8 | Vérifier l'API : `curl http://localhost:8000/health` | `{"status": "healthy"}` |
| 9 | Accéder à Streamlit : `http://server:8501` | Dashboard visible |
| 10 | Accéder à Grafana : `http://server:3000` | Login OK |

### 6.4 Health checks

| Service | Endpoint / Commande | Fréquence | Timeout |
|---------|-------------------|-----------:|--------:|
| PostgreSQL | `pg_isready` | 10s | 5s |
| FastAPI | `GET /health` | 30s | 10s |
| Streamlit | `HTTP GET :8501` | 30s | 10s |
| Grafana | `HTTP GET :3000/api/health` | 30s | 10s |
| Mosquitto | `mosquitto_sub -t '$SYS/#'` | 60s | 10s |

---

## 7. Plan de rollback

### 7.1 Critères de déclenchement

Un rollback est déclenché si **l'un** des critères suivants est atteint :

| Critère | Seuil | Responsable décision |
|---------|:-----:|---------------------|
| Perte de données capteurs | > 30% pendant > 1h | Équipe technique |
| Fausses alertes critiques | > 5 en 24h | Responsable maintenance |
| Indisponibilité API | > 2h continue | Équipe technique |
| Impact production négatif | Tout arrêt causé par la solution | Direction industrielle |
| Rejet massif des utilisateurs | > 50% refusent d'utiliser | Chef de projet |

### 7.2 Procédure de rollback

```mermaid
graph TD
    A["🚨 Détection du problème"] --> B{"Gravité ?"}
    B -->|Mineur| C["Correction à chaud<br/>(hotfix)"]
    B -->|Majeur| D["Rollback partiel<br/>(désactivation alerting)"]
    B -->|Critique| E["Rollback complet<br/>(retour mode curatif)"]
    
    C --> F["Monitoring renforcé<br/>(24h)"]
    D --> G["Diagnostic<br/>+ correctif"]
    E --> H["Communication<br/>aux utilisateurs"]
    
    G --> I["Redéploiement<br/>après correction"]
    H --> J["Plan de reprise<br/>avec date de redéploiement"]
    
    F --> K["✅ Retour à la normale"]
    I --> K
    J --> K
```

### 7.3 Procédure technique de rollback

| Étape | Action | Commande |
|:-----:|--------|---------|
| 1 | Arrêter les containers | `docker compose down` |
| 2 | Restaurer la version précédente du code | `git checkout <tag_précédent>` |
| 3 | Restaurer la BDD (si nécessaire) | `pg_restore -d mecha_predict backup_<date>.dump` |
| 4 | Redémarrer avec l'ancienne version | `docker compose up -d` |
| 5 | Vérifier les health checks | `docker compose ps` |
| 6 | Notifier les utilisateurs | Email + message dashboard |

### 7.4 Communication en cas de rollback

| Destinataire | Canal | Message type |
|-------------|-------|-------------|
| Responsables maintenance | Email + téléphone | « La solution est temporairement désactivée. Reprenez les procédures de maintenance habituelles. Nous vous informerons de la reprise. » |
| Opérateurs | Affichage usine | « Maintenance prédictive en pause. Signalez tout problème machine à votre chef d'équipe. » |
| Direction | Email | « Rapport d'incident avec analyse de cause, plan de correction et planning de reprise. » |

---

## 8. Impacts organisationnels

### 8.1 Changements de processus

| Processus | Avant | Après |
|-----------|-------|-------|
| Détection de panne | Visuel / Auditif par l'opérateur | Alerte automatique IA + expertise terrain |
| Décision d'intervention | Réactif (urgence) | Proactif (planifié selon RUL) |
| Planification maintenance | Calendrier constructeur (systématique) | Basée sur l'état réel de la machine |
| Stock pièces de rechange | Sur-stockage préventif | Commande ciblée selon les prédictions |
| Reporting | Manuel (Excel mensuel) | Automatique (dashboard temps réel) |

### 8.2 Nouveaux rôles et responsabilités

| Rôle | Responsabilité | Profil |
|------|----------------|--------|
| **Administrateur MECHA Predict** | Configuration, mises à jour, support technique | IT (1 personne, Lyon) |
| **Super-utilisateur** (par site) | Formation locale, support de proximité | Responsable maintenance |
| **Ambassadeur** (par site) | Relais terrain, remontée de feedback | Technicien volontaire |

---

## 9. Points de vigilance et risques

| N° | Risque | Probabilité | Impact | Mitigation |
|----|--------|:-----------:|:------:|-----------|
| R1 | Connectivité réseau instable (sites distants) | Moyenne | Élevé | Buffer local (Edge Gateway), mode dégradé |
| R2 | Incompatibilité capteurs existants | Faible | Moyen | Audit préalable, gateway Modbus→MQTT |
| R3 | Modèle ML peu performant sur certains types de machines | Moyenne | Moyen | Calibration par type, re-entraînement fréquent |
| R4 | Résistance des équipes terrain | Élevée | Élevé | Plan de conduite du changement (cf. change_management.md) |
| R5 | Surcharge serveur central (50 machines) | Faible | Moyen | Dimensionnement validé, scaling possible |
| R6 | Perte de données en cas de panne serveur | Faible | Élevé | Backup quotidien, réplication optionnelle |
| R7 | Non-conformité réglementaire (Espagne) | Faible | Élevé | Audit juridique avant Phase 3 |

---

## 10. Critères de validation — Go/No-Go par phase

### Matrice Go/No-Go

| Critère | Poids | Phase 1→2 | Phase 2→3 | Phase 3→4 |
|---------|:-----:|:---------:|:---------:|:---------:|
| Infrastructure opérationnelle | 20% | ✅ requis | ✅ requis | ✅ requis |
| Données capteurs reçues ≥ 95% | 20% | ✅ requis | ✅ requis | ✅ requis |
| Accuracy modèle ≥ 80% | 20% | ✅ requis | ✅ requis | ✅ requis |
| Fausses alertes ≤ 15% | 15% | ✅ requis | ✅ requis | ✅ requis |
| Adoption utilisateur ≥ 60% | 15% | ✅ requis | ✅ requis | ✅ requis |
| Satisfaction ≥ 6/10 | 10% | ⚠️ souhaité | ✅ requis | ✅ requis |

### Processus de décision

```mermaid
graph LR
    A["Fin de phase"] --> B["Collecte des<br/>métriques"]
    B --> C["Évaluation<br/>Go/No-Go"]
    C --> D{"Tous critères<br/>✅ requis OK ?"}
    D -->|Oui| E["✅ GO<br/>Phase suivante"]
    D -->|Non| F{"Critères<br/>bloquants ?"}
    F -->|Oui| G["❌ NO-GO<br/>Plan de correction"]
    F -->|Non| H["⚠️ GO conditionnel<br/>avec actions correctives"]
    G --> I["Correction<br/>(2-4 semaines)"]
    I --> C
```

---

> **Document validé par** : Équipe projet MECHA  
> **Prochaine révision** : Avant le lancement de la Phase 1
