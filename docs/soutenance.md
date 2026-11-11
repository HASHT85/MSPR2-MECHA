# Support et Conducteur de Soutenance Orale — MSPR 2 MECHA Predict

> **Certification** : RNCP35584 (Niveau 7) — Expert en Informatique et Système d'Information (EPSI)  
> **Épreuve** : MSPR **TPRE841** — Bloc 4 : *Concevoir et développer des solutions applicatives métier et spécifiques* (`C1` à `C8`)  
> **Format officiel** : **20 minutes de présentation en équipe** + **30 minutes d'échanges individuels et collectifs avec le jury**  
> **Équipe (maîtrise croisée intégrale C1–C8)** : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel  
> **Fichiers diaporama associés** : `livrables/03_Support_Soutenance/Support_Soutenance_MECHA_TPRE841.pptx` & `.pdf` (16 slides 16:9)

---

## Répartition Chronométrée des 20 Minutes (4 × 5 min)

> **Règle d'or évaluation individuelle** : chaque membre présente un bloc cohérent de **5 minutes** mais maîtrise l'intégralité des 8 compétences (`C1`–`C8`) et des **3 extraits de code clés** pour répondre individuellement aux questions du jury durant les 30 minutes d'échange.

| Séquence | Intervenant proposé | Durée | Slides | Compétences démontrées |
|----------|---------------------|:-----:|:------:|------------------------|
| **Partie 1** | **Malek El Fayedh** | `00:00 – 05:00` | Slides 1 à 4 | Contexte industriel, continuité **TPRE831 -> TPRE841**, recueil besoins **C1**, architecture 7 couches & SCADA/MES/NTP **C2** |
| **Partie 2** | **Thibaut Doreau** | `05:00 – 10:00` | Slides 5 à 8 | Pipeline données hybrides publiques (110k), anti-fuite, 5 modèles ML **C3**, analyse **AMDEC**, **Extrait de code #1** |
| **Partie 3** | **Vincent Gonçalves** | `10:00 – 15:00` | Slides 9 à 12 | Solution intégrée **C4** (API 9 routes, formalisme YAML/JSON/SQL, Streamlit 6 vues + Grafana), **Extraits de code #2 & #3**, tests **C5** (104 tests) & CI/CD **C6** |
| **Partie 4** | **Pierre-Louis Guinel** | `15:00 – 20:00` | Slides 13 à 16 | Conformité & guide métier 2 pages **C7**, conduite du changement & outil in-app **C8**, RGPD / EU AI Act, déploiement multi-sites & ROI |

---

## Détail Slide par Slide (16 Slides)

### Slide 1 — Titre & Continuité du Projet
- **MECHA Predict** : Plateforme industrielle de maintenance prédictive par IA (5 usines FR/ES, 50 machines MECHA).
- Passage du cadrage et PoC (**MSPR TPRE831**) à la solution applicative intégrée, conteneurisée et validée (**MSPR TPRE841**).

### Slide 2 — Problématique Industrielle MECHA & Enjeux Économiques
- **5 sites** : Lyon (siège), Toulouse, Nantes (60 % Aéronautique EN 9100) + Barcelone, Madrid (40 % Automobile IATF 16949).
- **Douleur métier** : 70 % de maintenance curative, données silotées (SCADA / MES / ERP), 12 à 18 arrêts non planifiés/mois, **2,4 M EUR/an** de budget maintenance et **180 k EUR** de pénalités contractuelles.
- **Cibles** : disponibilité `>= 95 %`, arrêts `< 4 h/mois`, ROI estimé **200 à 300 k EUR/an** (< 12 mois).

### Slide 3 — Collecte et Formalisation des Besoins Métiers (Compétence C1)
- Entretien semi-directif structuré (2h30, 6 axes A–F, 24 questions) avec M. Duval (Directeur Industriel) et Mme Martin (Resp. Maintenance Lyon).
- Méthode de transcription en 4 étapes : *Verbatims -> Pain Points -> Priorisation MoSCoW (10 BF) -> Exigences mesurables (7 BNF)*.
- Livrable : `docs/client_interview.md` (`01_Entretien_Client_Besoins_C1.pdf`).

### Slide 4 — Architecture Applicative en 7 Couches & Critères C2 (Compétence C2)
- Acquisition **IoT + SCADA + MES** synchronisés en **UTC via NTP**, stockage **PostgreSQL 15** (`4` tables, vue `v_machine_status`, `11` index), API **FastAPI**, **Streamlit (6 vues)** + **Grafana (3 dashboards)**.
- Justification formelle des 4 propriétés C2 :
  - **Stabilité** : conteneurs isolés, validation Pydantic stricte, transactions ACID.
  - **Efficacité** : inférence batch < 25 ms, index B-Tree, modèles compressés (32 Mo).
  - **Pérennité** : découplage REST, standards open-source, trajectoire TimescaleDB / MLflow.
  - **Tolérance aux pannes** : triple fallback (`Random Forest -> XGBoost -> heuristique`), mode dégradé UI, healthchecks Docker.

### Slide 5 — Ingénierie des Données & Conformité Sujet (110 000 lignes)
- **100 000 mesures simulées MECHA** (4 profils machines, cycles jour/nuit, dégradation physique) + **10 000 mesures publiques communautaires UCI AI4I 2020** (*CC BY 4.0*, zéro donnée confidentielle réelle).
- **6 features temporelles enrichies** (`temp_rolling_10min`, `temp_trend_1h`, `vibr_rolling_10min`, `temp_std_30min`, `energy_vibr_ratio`, `downtime_risk`).
- Typage entier strict (`Int64`) garantissant l'ingestion directe `\COPY` PostgreSQL sans flottants parasites.

### Slide 6 — Modélisation IA sans Fuite de Données & Résultats (Compétence C3)
- **Correction majeure post-revue** : exclusion stricte de `machine_status`, `predicted_remaining_life` et `downtime_risk` des entrées ML + **split temporel 80/20 stratifié par source** (`88 000` train / `22 000` test).
- **Random Forest** (principal) : **F1 = 80.4 %**, **Rappel = 90.0 %**, **AUC = 0.988** (priorité métier au rappel pour éviter les pannes non détectées).
- **XGBoost** (secours) : **F1 = 81.1 %**, **AUC = 0.988**.
- **RF Regressor RUL** : **MAE = 26.9 min**, **R² = 0.719** | **Isolation Forest** : **AUC = 0.839**.
- Transparence scientifique : F1 = 82.2 % sur simulé MECHA vs 7.3 % sur UCI AI4I (pannes AI4I liées au couple et à l'usure d'outil hors des 10 capteurs communs).

### Slide 7 — Analyse AMDEC (Machines & Système IA)
- 5 modes de défaillance analysés : *Surchauffe* (criticité `60 -> 24`), *Vibration roulements* (`48 -> 24`), *Chute de pression* (`36 -> 18`), *Usure outil* (`24 -> 8`), *Défaut électrique* (`20 -> 12`) -> **-50 % de criticité moyenne**.
- AMDEC du système IA : mitigation des faux négatifs (rappel 90 % + Isolation Forest) et des faux positifs (*Human-in-the-Loop*).

### Slide 8 — Maîtrise du Code (C3/C4) : Extrait #1 — Anti-Leakage & Split Temporel (`train_models.py`)
```python
# models/training/train_models.py — Garantie zéro Data Leakage sur les 10 features capteurs
LEAKY_FEATURES = ["machine_status", "predicted_remaining_life", "downtime_risk"]
FEATURES = [
    "temperature", "vibration", "humidity", "pressure", "energy_consumption",
    "temp_rolling_10min", "temp_trend_1h", "vibr_rolling_10min",
    "temp_std_30min", "energy_vibr_ratio",
]
# Split chronologique 80/20 appliqué séparément sur chaque source (MECHA + UCI AI4I)
for _, group in df.groupby("data_source", sort=False):
    group_sorted = group.sort_values("timestamp")
    split_idx = int(len(group_sorted) * TRAIN_RATIO)
    train_parts.append(group_sorted.iloc[:split_idx])
    test_parts.append(group_sorted.iloc[split_idx:])
```

### Slide 9 — Solution Applicative Intégrée & Formalisme de Configuration (Compétence C4)
- **API FastAPI (`api/main.py`)** : 9 routes REST, validation Pydantic, clé `X-API-Key`.
- **Formalisme déclaratif C4** :
  1. Provisioning YAML Grafana (`datasource.yml`, `dashboard.yml`) ;
  2. Dashboards JSON versionnés par rôle + vue SQL `v_machine_status` ;
  3. Paramétrage dynamique à chaud des seuils métiers via `GET/PUT /alerts/config` ;
  4. Règles de transformation des probabilités en niveaux d'urgence (`low/medium/high/critical`, RUL `urgent/soon/moderate/safe`).

### Slide 10 — Maîtrise du Code (C3/C4) : Extraits #2 & #3 — Chaîne de Fallback API & Human-in-the-Loop
```python
# Extrait #2 : api/main.py — Inférence résiliente avec chaîne de triple fallback
if models.classifier is not None:
    proba = models.classifier.predict_proba(features)
    prediction, confidence = _decide(proba)
    model_name = "random_forest"
elif models.xgboost is not None:
    proba = models.xgboost.predict_proba(features)
    prediction, confidence = _decide(proba)
    model_name = "xgboost"
else:
    prediction, confidence = _mock_predict(features)  # Continuité de service garantie
```
```python
# Extrait #3 : app/src/dashboard.py — Mise à jour dynamique des seuils C4 depuis l'UI
updated = api_put("/alerts/config", {
    "temperature_critical": float(new_temp_crit),
    "defect_rate_critical": float(new_defect),
    "trs_minimum": float(new_trs),
    "anomaly_rate_warning": float(new_anom),
})
```

### Slide 11 — Interfaces Métiers : 6 Vues Streamlit + 3 Dashboards Grafana
- **Grafana OSS** : *DG Groupe* (TRS, benchmark 5 sites), *Directeur d'Usine* (jauges temps réel), *Technicien* (plan d'action prioritaire).
- **Streamlit** : *Groupe*, *Site*, *Machine*, *Alertes*, *Modèle IA*, et **6e vue `Accompagnement`** dédiée à la qualification terrain *Human-in-the-Loop* (C8) et au paramétrage dynamique (C4).

### Slide 12 — Tests Automatisés (C5) & Intégration Continue (C6)
- **104 tests automatisés (`100 % PASS`, `0 skipped`)** :
  - `21` tests qualité données & compatibilité SQL `\COPY` ;
  - `16` tests modèles ML & alignement entraînement <-> API ;
  - `61` tests endpoints API (**87 % de couverture** sur `api/main.py`) ;
  - `6` tests d'intégration bout-en-bout + plan de correction `CORR-01..05`.
- **Pipeline GitHub Actions (`.github/workflows/ci.yml`)** : 3 jobs séquentiels bloquants (*Ruff Lint/Format -> Régénération Data/ML + 104 tests Pytest -> Build Docker multi-images*).

### Slide 13 — Conformité Fonctionnelle & Guide Utilisateur Métier 2 Pages (Compétence C7)
- Matrice de conformité exhaustive validant 100 % des exigences du cahier des charges TPRE841.
- **Guide utilisateur métier synthétique de 2 pages A4** (`07_Guide_Utilisateur_Metier_2pages_C7.pdf`) rédigé sans jargon data pour les équipes maintenance : lecture des codes couleurs, procédure de réaction en 4 étapes, limites d'usage.

### Slide 14 — Conduite du Changement & Outil Opérationnel In-App (Compétence C8)
- Démarche structurée autour des **4 axes** (*Informer, Communiquer, Former, Faire participer*), de la **FutureWheel** et du modèle transitionnel de **William Bridges**.
- **Concrétisation logicielle C8** : onglet Streamlit **Accompagnement** permettant aux techniciens de qualifier chaque alerte IA sans donnée nominative (RGPD), de consulter les fiches réflexes par rôle et de suivre les KPIs d'adoption.

### Slide 15 — Conformité Réglementaire (RGPD, EU AI Act) & Déploiement Multi-Sites
- **RGPD** : données capteurs machines uniquement, zéro profilage opérateur, registre de traitement et PIA conditionnel documentés.
- **EU AI Act (2024/1689)** : système d'aide à la décision à risque limité, 5 *Model Cards*, supervision *Human-in-the-Loop* obligatoire.
- **Déploiement 12 mois** : Phase 1 Pilote Lyon (10 machines) -> Phase 2 Toulouse/Nantes (+20) -> Phase 3 Barcelone/Madrid (+20, i18n ES) -> Phase 4 Stabilisation, avec critères Go/No-Go et Rollback < 15 min.

### Slide 16 — Bilan, Usage Critique de l'IA Générative & ROI
- **100 % des livrables prêts et vérifiés** : dépôt Git structuré, Docker Compose auto-initialisé, 104 tests verts, 10 livrables PDF individuels + rapport consolidé.
- **Usage raisonné et audité de l'IA générative** : détection et correction par l'équipe du *data leakage* initial et du typage flottant SQL.
- **Impact économique** : **200 à 300 k EUR/an** d'économies projetées pour **150 k EUR** d'investissement initial (**ROI < 12 mois**).
