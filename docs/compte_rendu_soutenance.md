# Compte-Rendu de Soutenance — MSPR 2 MECHA Predict

> **Certification** : RNCP35584 — Expert en Informatique et Systeme d'Information  
> **Bloc 4** : Concevoir et developper des solutions applicatives metier et specifiques  
> **Reference** : MSPR TPRE841  
> **Date** : Mai 2026  
> **Equipe** : Malek El Fayedh, Thibaut Doreau, Vincent Goncalves, Pierre-Louis Guinel  
> **Formation** : EPSI — Promotion 2026

---

## Table des matieres

1. [Contexte et problematique industrielle](#1-contexte-et-problematique-industrielle)
2. [Collecte des besoins metiers (C1)](#2-collecte-des-besoins-metiers-c1)
3. [Architecture de la solution (C2)](#3-architecture-de-la-solution-c2)
4. [Pipeline de donnees et feature engineering](#4-pipeline-de-donnees-et-feature-engineering)
5. [Modelisation et intelligence artificielle (C3)](#5-modelisation-et-intelligence-artificielle-c3)
6. [AMDEC — Analyse des Modes de Defaillance](#6-amdec--analyse-des-modes-de-defaillance)
7. [Solution applicative integree (C4)](#7-solution-applicative-integree-c4)
8. [Tests et validation (C5)](#8-tests-et-validation-c5)
9. [Integration continue (C6)](#9-integration-continue-c6)
10. [Documentation et conformite (C7)](#10-documentation-et-conformite-c7)
11. [Conduite du changement (C8)](#11-conduite-du-changement-c8)
12. [Conformite reglementaire — RGPD et EU AI Act](#12-conformite-reglementaire--rgpd-et-eu-ai-act)
13. [Plan de deploiement multi-sites](#13-plan-de-deploiement-multi-sites)
14. [Bilan et perspectives](#14-bilan-et-perspectives)
15. [Annexes](#15-annexes)

---

## 1. Contexte et problematique industrielle

### 1.1 Presentation de l'entreprise MECHA

MECHA est un groupe industriel fictif specialise dans la fabrication discrete de pieces mecaniques de haute precision, destinees aux secteurs de l'aeronautique (60% du chiffre d'affaires) et de l'automobile (40%). Le groupe exploite **5 usines** reparties entre la France et l'Espagne, totalisant **50 machines industrielles** equipees de capteurs IoT.

| Site | Ville | Pays | Machines | Specialite | Date d'ouverture |
|------|-------|------|----------|------------|-----------------|
| USN-FR-01 | Lyon | France | 10 | Aeronautique + Automobile (siege) | Mars 2018 |
| USN-FR-02 | Toulouse | France | 10 | Aeronautique | Juin 2019 |
| USN-FR-03 | Nantes | France | 10 | Aeronautique | Janvier 2021 |
| USN-ES-01 | Barcelone | Espagne | 10 | Automobile | Septembre 2022 |
| USN-ES-02 | Madrid | Espagne | 10 | Automobile | Avril 2023 |

Le modele economique repose sur des contrats pluriannuels avec des constructeurs automobiles europeens, des equipementiers et des acteurs aeronautiques de rang 1 et 2. Les exigences clients portent sur la tracabilite complete, les indicateurs de performance (taux de rebuts, disponibilite machines, temps de cycle) et la reactivite aux derives qualite. Les normes applicables sont EN 9100 pour l'aeronautique et IATF 16949 pour l'automobile.

### 1.2 Problematique identifiee

L'analyse conduite en MSPR 1 a permis d'identifier les problematiques suivantes :

| Probleme | Criticite | Impact |
|----------|-----------|--------|
| Donnees dispersees entre systemes SCADA, MES et ERP | Critique | Impossible d'avoir une vision consolidee |
| Absence de detection precoce des derives machines | Critique | 12 a 18 arrets non planifies par mois |
| Pas d'alertes operationnelles unifiees | Majeur | Delai detection-intervention de 4 a 8 heures |
| Aucun modele predictif deploye | Majeur | 70% de maintenance curative |
| Indicateurs non standardises entre les 5 sites | Moyen | Comparaison inter-sites impossible |

**Chiffres cles de la situation actuelle :**
- Budget maintenance annuel : 2,4 millions d'euros (8% du chiffre d'affaires)
- Repartition : 70% curatif / 25% preventif / 5% predictif
- Disponibilite machines : 87-88% (objectif secteur : 95%)
- Cout d'un arret non planifie : 5 000 a 15 000 euros (jusqu'a 30 000 euros en aeronautique)
- Penalites l'annee precedente : 180 000 euros (3 penalites contractuelles)
- Stock de pieces : 200 000 euros dont 30% inutilise

### 1.3 Objectifs du projet MSPR 2

La MSPR 2 constitue le passage du cadrage et de l'etude de faisabilite (MSPR 1) a la conception et la realisation concrete d'un prototype fonctionnel. Les objectifs sont les suivants :

| Indicateur | Situation actuelle | Objectif vise |
|------------|-------------------|---------------|
| Temps d'arret non planifie | Environ 12h par mois | Inferieur a 4h par mois |
| Taux de pannes critiques | Environ 8% | Inferieur a 3% |
| Precision des predictions | 0% (aucun modele) | Superieur a 90% |
| Repartition maintenance | 70% curatif | 50% predictif |
| Disponibilite machines | 87-88% | Superieur a 95% |
| ROI estime | — | 200 000 a 300 000 euros par an |

### 1.4 Continuite avec la MSPR 1

Les recommandations formulees en MSPR 1 ont ete systematiquement prises en compte en MSPR 2 :

| Recommandation MSPR 1 | Action MSPR 2 | Statut |
|------------------------|---------------|--------|
| Ameliorer le rappel du Random Forest (F1=71%) | Seuil abaisse a 0.3, features temporelles ajoutees, F1 passe a 76.3% | Appliquee |
| Ajouter des features temporelles (moyenne mobile, tendance) | 6 features enrichies (temp_rolling_10min, temp_trend_1h, etc.) | Appliquee |
| Tester XGBoost | XGBoost entraine et compare (F1=75.9%, AUC=90.5%) | Appliquee |
| Exclure machine_status (data leakage) | Exclu du pipeline ML, test anti-leakage automatise | Appliquee |
| Documenter unites et encodages | Dictionnaire de donnees complet (data_dictionary.md) | Appliquee |
| Enrichir donnees contextuelles | Ligne production, type piece, profil machine ajoutes | Appliquee |
| Human-in-the-Loop pour EU AI Act | Mention explicite dans dashboard et API | Appliquee |
| Conteneuriser la solution | Docker Compose avec 4 services | Appliquee |
| Integration continue | GitHub Actions (lint, test, build) | Appliquee |
| Deploiement progressif | Plan 4 phases sur 12 mois documente | Appliquee |
| Conduite du changement | Document complet avec 4 axes et modeles de reference | Appliquee |

---

## 2. Collecte des besoins metiers (C1)

### 2.1 Methodologie de collecte

La collecte des besoins a ete realisee par un entretien semi-directif de 2 heures 30 avec deux representants de la Direction Industrielle MECHA :

- **M. Jean-Pierre Duval** — Directeur Industriel (commanditaire du projet)
- **Mme Sophie Martin** — Responsable Maintenance de l'usine de Lyon

Le questionnaire a ete structure en 6 axes thematiques (A a F) comprenant 24 questions :
- Axe A : Organisation et processus actuels
- Axe B : Donnees et systemes d'information
- Axe C : Besoins fonctionnels
- Axe D : Contraintes et exigences
- Axe E : Attentes et criteres de succes
- Axe F : Deploiement et changement

### 2.2 Besoins fonctionnels identifies

L'entretien a permis d'identifier 10 besoins fonctionnels, priorises selon la methode MoSCoW :

| Ref. | Besoin | Priorite |
|------|--------|----------|
| BF-01 | Dashboard consolide multi-sites avec KPIs temps reel | Must |
| BF-02 | Alertes automatiques sur derives machines | Must |
| BF-03 | Prediction de pannes avec estimation du delai | Must |
| BF-04 | Historique de maintenance consultable | Must |
| BF-05 | Comparaison inter-sites (benchmark) | Must |
| BF-06 | Detection d'anomalies comportementales | Must |
| BF-07 | Indicateurs de degradation par machine | Must |
| BF-08 | Reporting mensuel automatise | Should |
| BF-09 | Integration future avec GMAO | Should |
| BF-10 | Application mobile pour techniciens terrain | Should |

### 2.3 Besoins non-fonctionnels

| Ref. | Exigence | Seuil |
|------|----------|-------|
| BNF-01 | Disponibilite du systeme | Superieur ou egal a 99.5% |
| BNF-02 | Temps de reponse interface | Inferieur a 3 secondes |
| BNF-03 | Hebergement des donnees | Europe (RGPD) |
| BNF-04 | Tracabilite des actions | Complete (normes aeronautiques) |
| BNF-05 | Scalabilite | 50 a 200 machines |
| BNF-06 | Securite | Authentification, chiffrement |
| BNF-07 | Simplicite d'utilisation | Formation inferieure a 4 heures |

### 2.4 Verbatim cle du commanditaire

> "Le succes, c'est quand mes responsables maintenance me diront : 'je ne peux plus travailler sans cet outil'." — M. Duval, Directeur Industriel

---

## 3. Architecture de la solution (C2)

### 3.1 Architecture en 7 couches

L'architecture retenue est une architecture en couches, distribuee et tolerante aux pannes, concue pour un environnement industriel :

![Architecture en 7 couches MECHA Predict](docs/images/diag_architecture.png)

### 3.2 Justification des choix techniques

Chaque composant a fait l'objet d'un comparatif documente avec au minimum 3 alternatives :

| Composant | Choix retenu | Alternatives evaluees | Critere decisif |
|-----------|-------------|----------------------|-----------------|
| Langage | Python 3.11 | R, Java, Julia | Ecosysteme ML + API unifie, competences equipe |
| Framework ML | scikit-learn | TensorFlow, PyTorch, H2O.ai | Modeles interpretables, prototypage rapide, donnees tabulaires |
| Classification | Random Forest | SVM, Regression logistique | Robuste, interpretable, peu de pretraitement |
| Regression RUL | XGBoost | LSTM, SVR | Performance elevee, gestion donnees manquantes |
| Framework API | FastAPI | Flask, Django REST, Express.js | Performance (15k req/s), doc Swagger native, validation Pydantic |
| Dashboard analytique | Streamlit | Dash, Metabase, Power BI | Prototypage Python, integration ML native |
| Monitoring temps reel | Grafana | Kibana, Datadog | Standard industriel, alerting natif, connexion PostgreSQL |
| Base de donnees | PostgreSQL 16 | MongoDB, InfluxDB, TimescaleDB | Polyvalent, extensible, ACID, connexion Grafana native |
| Conteneurisation | Docker + Compose | Kubernetes, VM, Podman | Simple, reproductible, adapte a l'echelle du PoC |
| CI/CD | GitHub Actions | Jenkins, GitLab CI, CircleCI | Integration native GitHub, zero infrastructure |

### 3.3 Strategie a deux dashboards — Evolution MSPR 2

En MSPR 1, Grafana a ete retenu comme unique outil de restitution. En MSPR 2, Streamlit a ete ajoute comme couche d'analyse complementaire :

| Besoin | Grafana | Streamlit |
|--------|---------|-----------|
| Monitoring temps reel des capteurs | Excellent | Limite (pas de refresh auto) |
| Alertes operationnelles (email/Slack) | Natif | Non supporte |
| Exploration interactive des donnees | Limite (SQL fige) | Filtres dynamiques Python |
| Visualisation des predictions ML | Pas d'integration ML | Chargement natif des modeles scikit-learn |
| Comparaison de modeles (F1, AUC-ROC) | Non supporte | Courbes ROC, matrice de confusion |
| Feature importance et explicabilite IA | Non supporte | Graphiques interactifs |
| Vue consolidee multi-sites avec drill-down | Limite (variables) | Navigation Groupe, Site, Machine |

### 3.4 Dimensionnement

| Metrique | Pilote (Lyon) | Complet (5 sites) |
|----------|--------------|-------------------|
| Machines monitorees | 10 | 50 |
| Mesures par jour | 864 000 | 4 320 000 |
| Volume BDD par mois | 2 Go | 10 Go |
| Predictions par jour | 240 | 1 200 |
| Utilisateurs simultanes | 5 a 10 | 30 a 50 |

### 3.5 Schema de la base de donnees

La base PostgreSQL comprend 4 tables et 1 vue materialisee :

![Schema de la base de donnees MECHA](docs/images/diag_database.png)

9 index ont ete crees pour optimiser les requetes frequentes (par machine, par usine, par timestamp, par statut de maintenance).

---

## 4. Pipeline de donnees et feature engineering

### 4.1 Construction du dataset hybride

Le dataset final combine deux sources de donnees :

**Source 1 — Dataset MECHA simule (100 000 enregistrements)**
- 50 machines (IDs 1 a 50) reparties sur 5 usines
- Periode : a partir du 1er janvier 2025
- 2 000 enregistrements par machine
- Simulation realiste : cycle journalier (production 6h-22h, arret la nuit), degradation progressive, surchauffe, reparations

**Source 2 — Dataset AI4I 2020 Predictive Maintenance (10 000 enregistrements)**
- Provenance : UCI Machine Learning Repository / Kaggle
- 10 000 enregistrements issus de machines reelles
- Machines IDs 51 a 100
- Harmonisation des colonnes : temperature Kelvin vers Celsius, vitesse rotationnelle vers vibration, types de pannes adaptes au contexte MECHA

**Dataset final** : 110 000 enregistrements, 30 colonnes, 100 machines, 5 usines

### 4.2 Profils de machines

L'heterogeneite du parc industriel a ete modelisee par 4 profils distincts :

| Profil | Temperature de base | Vibration de base | Probabilite de panne | Probabilite maintenance preventive |
|--------|-------------------|-------------------|---------------------|-----------------------------------|
| Robuste | 70 degres C | 35 mm/s | 2% | 5% |
| Standard | 75 degres C | 40 mm/s | 4% | 8% |
| Fragile | 82 degres C | 50 mm/s | 8% | 12% |
| Vieillissante | 85 degres C | 55 mm/s | 10% | 15% |

### 4.3 Feature engineering

6 features enrichies ont ete ajoutees conformement aux recommandations de la MSPR 1 :

| Feature | Formule | Justification |
|---------|---------|---------------|
| temp_rolling_10min | Moyenne mobile temperature (fenetre 10 min) | Lisser le bruit des capteurs |
| temp_trend_1h | Pente lineaire de la temperature (fenetre 1h) | Detecter une montee progressive |
| vibr_rolling_10min | Moyenne mobile vibration (fenetre 10 min) | Lisser les pics ponctuels |
| temp_std_30min | Ecart-type temperature (fenetre 30 min) | Detecter l'instabilite |
| energy_vibr_ratio | Rapport energie / vibration | Correlations croisees |
| downtime_risk | 0.3 x temp_risk + 0.25 x vibr_risk + 0.45 x rul_risk | Score composite de risque d'arret |

### 4.4 Variables les plus predictives

L'analyse des correlations avec la variable cible `maintenance_required` a revele :

| Variable | Correlation | Interpretation |
|----------|------------|----------------|
| predicted_remaining_life | -0.34 (tres forte) | Plus le RUL diminue, plus le risque augmente |
| temperature | +0.28 (forte) | Temperature elevee = indicateur de panne |
| vibration | +0.11 (moderee) | Vibrations anormales = usure mecanique |
| humidity | ~0.00 (nulle) | Non informative |
| pressure | ~0.00 (nulle) | Non informative |

### 4.5 Dictionnaire de donnees

Un dictionnaire de donnees complet (data_dictionary.md) documente les 30 colonnes du dataset, incluant pour chaque variable : le type, la plage de valeurs, l'unite, la source et la correlation avec la variable cible. Les 9 hypotheses de simulation sont egalement documentees.

---

## 5. Modelisation et intelligence artificielle (C3)

### 5.1 Strategie de modelisation

Trois types de problemes de maintenance predictive sont couverts :

| Probleme | Type | Modele | Sortie |
|----------|------|--------|--------|
| "Cette machine va-t-elle tomber en panne ?" | Classification binaire | Random Forest, XGBoost, Regression Logistique | 0 (normal) / 1 (maintenance requise) + probabilite |
| "Dans combien de temps ?" | Regression | RF Regressor RUL | Nombre d'heures estimees avant panne |
| "Le comportement est-il anormal ?" | Detection d'anomalies | Isolation Forest | Score d'anomalie + severite |

### 5.2 Protocole d'entrainement

**Split temporel 80/20** : Les donnees sont triees par timestamp. Les 80% les plus anciennes constituent le jeu d'entrainement (88 000 enregistrements), les 20% les plus recentes constituent le jeu de test (22 000 enregistrements). Ce choix evite le data leakage temporel qu'un split aleatoire aurait introduit.

**Features utilisees** (12) : temperature, vibration, humidity, pressure, energy_consumption, predicted_remaining_life, temp_rolling_10min, temp_trend_1h, vibr_rolling_10min, temp_std_30min, energy_vibr_ratio, downtime_risk

**Variable exclue** : `machine_status` — cette variable a ete identifiee en MSPR 1 comme source de data leakage. Un test automatise verifie son exclusion.

**Gestion du desequilibre** : La classe positive (maintenance requise) represente seulement 3.1% des echantillons (908 sur 22 000 dans le jeu de test). Deux techniques sont appliquees :
- Random Forest : parametre `class_weight='balanced'`
- XGBoost : parametre `scale_pos_weight` calcule automatiquement (ratio negatifs/positifs)

**Reproductibilite** : `RANDOM_STATE=42` pour tous les modeles

### 5.3 Resultats des 5 modeles

#### Modeles de classification

| Metrique | Random Forest | XGBoost | Regression Logistique |
|----------|:------------:|:-------:|:--------------------:|
| Accuracy | 98.4% | 98.4% | 90.5% |
| Precision | 98.8% | 97.9% | 27.3% |
| Recall | 62.1% | 62.0% | 79.2% |
| F1-Score | 76.3% | 75.9% | 40.6% |
| AUC-ROC | 0.898 | 0.905 | 0.868 |
| Faux positifs | 7 | 12 | 1 912 |
| Faux negatifs | 344 | 345 | 189 |
| Vrais positifs | 564 | 563 | 719 |

**Analyse** : Le Random Forest et le XGBoost atteignent des performances quasi-identiques. Le Random Forest est retenu comme modele principal en raison de sa meilleure interpretabilite (feature importance native). Le XGBoost sert de modele de secours (meilleur AUC-ROC : 0.905 contre 0.898).

La Regression Logistique sert de baseline. Son recall eleve (79.2%) mais sa precision tres faible (27.3%) la rendent inutilisable en production (trop de fausses alertes).

#### Modele de detection d'anomalies

| Metrique | Isolation Forest |
|----------|:---------------:|
| Accuracy | 74.7% |
| Precision | 9.5% |
| Recall | 59.7% |
| AUC-ROC | 0.774 |
| Anomalies detectees | 5 735 |
| Contamination effective | 26.1% |

L'Isolation Forest, en tant que modele non supervise, a une precision faible mais permet de detecter des comportements atypiques sans labels prealables. Il est utilise en complement des modeles supervises.

#### Modele de regression RUL

| Metrique | RF Regressor RUL |
|----------|:----------------:|
| MAE | 39.25 heures |
| RMSE | 69.28 heures |
| R-carre | 0.598 (59.8%) |
| MSE | 4 799.84 |

Le modele RUL predit le temps restant avant defaillance avec une erreur moyenne de 39 heures. La categorisation est : urgent (inferieur a 24h), soon (inferieur a 72h), moderate (inferieur a 168h), safe (superieur ou egal a 168h).

### 5.4 Progression MSPR 1 vers MSPR 2

| Modele | F1 MSPR 1 | F1 MSPR 2 | Progression |
|--------|-----------|-----------|-------------|
| Random Forest | 71.0% | 76.3% | +5.3 points |
| Isolation Forest | 38.2% | 16.3% | -21.9 points (desequilibre accru) |
| Regression Logistique | 47.2% | 40.6% | -6.6 points (baseline) |
| XGBoost | Non teste | 75.9% | Nouveau |
| RF Regressor RUL | Non teste | R-carre=59.8% | Nouveau |

L'objectif MSPR 1 de F1 superieur ou egal a 75% est atteint pour le Random Forest (76.3%).

### 5.5 Top 3 des features les plus importantes

1. `predicted_remaining_life` — 37% d'importance
2. `downtime_risk` — 20% d'importance
3. `temp_rolling_10min` — 14% d'importance

### 5.6 Model Cards (conformite EU AI Act)

Chaque modele dispose d'une Model Card documentant : les hyperparametres, les metriques, les limites, les biais identifies, la classification EU AI Act (risque limite), les conditions de maintenance (reexamen trimestriel, reentrainement si baisse F1 superieure a 5%).

---

## 6. AMDEC — Analyse des Modes de Defaillance

### 6.1 Presentation de la demarche

L'AMDEC (Analyse des Modes de Defaillance, de leurs Effets et de leur Criticite) est une methode systematique d'analyse des risques utilisee dans l'industrie pour identifier les defaillances potentielles, evaluer leur gravite et definir des actions preventives. Dans le contexte de MECHA Predict, l'AMDEC est appliquee a deux niveaux :
- **Niveau machine** : analyse des modes de defaillance des equipements industriels
- **Niveau systeme IA** : analyse des risques lies au systeme de prediction

### 6.2 AMDEC des machines industrielles MECHA

L'analyse du dataset (110 000 enregistrements) a permis d'identifier 5 modes de defaillance, classes par criticite :

| Mode de defaillance | Frequence | Gravite | Detectabilite | Criticite (F x G x D) | Description |
|---------------------|:---------:|:-------:|:-------------:|:---------------------:|-------------|
| **Surchauffe (Overheating)** | 4 | 5 | 3 | **60** | Temperature superieure a 100 degres C, degradation progressive des composants mecaniques. Represente 35% des pannes observees. |
| **Probleme de vibration (Vibration Issue)** | 4 | 4 | 3 | **48** | Vibrations anormales dues a l'usure des roulements ou au desalignement. Represente 30% des pannes. 40% des pannes reelles sont liees aux roulements. |
| **Chute de pression (Pressure Drop)** | 3 | 3 | 4 | **36** | Perte de pression hydraulique ou pneumatique. Represente 20% des pannes. |
| **Defaut electrique (Electrical Fault)** | 2 | 5 | 2 | **20** | Court-circuit, surcharge, defaut d'isolation. Represente 15% des pannes. Gravite maximale car risque securite. |
| **Usure d'outil (Tool Wear Failure)** | 3 | 2 | 4 | **24** | Usure progressive de l'outil de coupe. Issu du dataset AI4I 2020. |

**Echelle de notation** : Frequence (1=rare, 5=tres frequent), Gravite (1=negligeable, 5=catastrophique), Detectabilite (1=toujours detecte, 5=indetectable)

### 6.3 Analyse des indicateurs de detection

Pour chaque mode de defaillance, les capteurs et seuils de detection sont definis :

| Mode de defaillance | Capteur principal | Seuil d'alerte | Seuil critique | Fenetre temporelle |
|---------------------|------------------|----------------|----------------|-------------------|
| Surchauffe | Temperature | Superieur a 90 degres C | Superieur a 100 degres C | Tendance sur 1h (temp_trend_1h) |
| Vibration | Vibration | Superieur a 50 mm/s | Superieur a 70 mm/s | Moyenne mobile 10 min (vibr_rolling_10min) |
| Chute de pression | Pression | Inferieur a 2.5 bar | Inferieur a 2.0 bar | Instantane |
| Defaut electrique | Energie | Superieur a 5 kW | Superieur a 7 kW | Ratio energie/vibration |
| Usure d'outil | Tool wear | Superieur a 180 min | Superieur a 220 min | Cumulatif |

### 6.4 Matrice de criticite

```
Gravite
  5 |         |         | Elec.   |         | Surch.  |
  4 |         |         |         | Vibr.   |         |
  3 |         |         | Press.  |         |         |
  2 |         |         | Outil   |         |         |
  1 |         |         |         |         |         |
    +---------+---------+---------+---------+---------+
      1         2         3         4         5
                    Frequence
```

### 6.5 Actions de mitigation par l'IA

| Mode de defaillance | Action IA | Modele utilise | Gain attendu |
|---------------------|-----------|---------------|--------------|
| Surchauffe | Alerte predictive 24-48h avant, recommandation arret preventif | Random Forest + RUL | Reduction de 60% des arrets pour surchauffe |
| Vibration | Detection precoce de desalignement, planification remplacement roulements | Isolation Forest + RF | Reduction de 40% des pannes de roulement |
| Chute de pression | Detection de fuite progressive | Isolation Forest | Detection 2h avant arret |
| Defaut electrique | Identification de surcharge anormale | Isolation Forest | Prevention des courts-circuits |
| Usure d'outil | Estimation du temps restant avant remplacement | RF Regressor RUL | Optimisation du stock de pieces |

### 6.6 AMDEC du systeme IA

| Mode de defaillance IA | Frequence | Gravite | Criticite | Mitigation |
|------------------------|:---------:|:-------:|:---------:|------------|
| Faux negatif (panne non detectee) | 3 | 5 | 15 | Seuil de prediction abaisse a 0.3 (vs 0.5), double validation par Isolation Forest |
| Faux positif (fausse alerte) | 2 | 2 | 4 | Precision de 98.8%, validation Human-in-the-Loop |
| Derive du modele (concept drift) | 3 | 4 | 12 | Monitoring F1 en production, reentrainement trimestriel |
| Donnees manquantes (capteur defaillant) | 3 | 3 | 9 | Imputation par mediane, mode fallback heuristique |
| Indisponibilite API | 2 | 4 | 8 | Health check toutes les 10s, redemarrage automatique Docker |
| Biais de profil machine | 2 | 3 | 6 | Entrainement avec class_weight balanced, 4 profils representes |

### 6.7 Impact de l'IA sur la criticite des defaillances

| Mode de defaillance | Criticite SANS IA | Criticite AVEC IA | Reduction |
|---------------------|:-----------------:|:-----------------:|:---------:|
| Surchauffe | 60 | 24 | -60% |
| Vibration | 48 | 24 | -50% |
| Chute de pression | 36 | 18 | -50% |
| Defaut electrique | 20 | 12 | -40% |
| Usure d'outil | 24 | 8 | -67% |

L'introduction de la maintenance predictive par IA reduit la criticite globale de 50% en moyenne, principalement grace a l'amelioration de la detectabilite (passage de detection reactive a detection predictive).

---

## 7. Solution applicative integree (C4)

### 7.1 API REST — FastAPI

L'API constitue le coeur de la solution applicative. Elle expose 9 endpoints REST :

| Methode | Route | Description | Modele ML |
|---------|-------|-------------|-----------|
| GET | /health | Health check (etat modeles, uptime) | — |
| POST | /predict | Prediction maintenance unitaire | Random Forest (fallback: XGBoost) |
| POST | /predict/batch | Prediction batch (max 100 machines) | Random Forest |
| POST | /predict/rul | Estimation RUL (heures restantes) | RF Regressor |
| POST | /anomaly | Detection d'anomalies | Isolation Forest |
| GET | /metrics | Metriques performance et statistiques API | — |
| GET | /model-info | Model Cards (EU AI Act) | — |
| GET | /alerts/config | Lecture des seuils d'alerte | — |
| PUT | /alerts/config | Modification des seuils d'alerte | — |

**Caracteristiques techniques** :
- 1 157 lignes de code
- 10 schemas Pydantic pour la validation des entrees/sorties
- Chaine de fallback : Random Forest, puis XGBoost, puis heuristique mock
- Categorisation automatique du risque : low, medium, high, critical
- Categorisation RUL : urgent (inferieur a 24h), soon (inferieur a 72h), moderate (inferieur a 168h), safe
- Authentification par cle API (header X-API-Key)
- CORS configurable
- Documentation Swagger auto-generee

### 7.2 Dashboard Streamlit — 5 vues metier

Le dashboard Streamlit (918 lignes, 34 675 octets) offre 5 vues adaptees aux differents profils utilisateurs :

**Vue 1 — Groupe (Direction Generale)**
KPIs consolides des 5 usines : TRS global, taux de maintenance, taux d'anomalies, nombre de machines actives, RUL moyen. Comparaison inter-sites et repartition des pannes par usine.

**Vue 2 — Site (Directeur d'Usine)**
Vue operationnelle par usine avec filtrage par site. KPIs du site, etat de chaque machine (profil, temperature, vibration, RUL, risque), alertes actives en temps reel.

![Vue Site Streamlit](docs/images/streamlit_site.png)

**Vue 3 — Machine (Equipe Maintenance)**
Diagnostic individuel d'une machine. Capteurs en temps reel (temperature, vibration, RUL sur 3 jours), jauge de score de risque d'arret (0-100%), facteurs de risque normalises.

![Vue Machine Streamlit](docs/images/streamlit_machine.png)

**Vue 4 — Alertes (Tous niveaux)**
Centre d'alertes avec filtres par usine, type et severite. Compteurs : alertes critiques, alertes majeures, total. Tableau detaille avec horodatage, machine, type, niveau et detail.

![Centre d'Alertes Streamlit](docs/images/streamlit_alertes.png)

**Vue 5 — Modele IA (Data Team)**
Comparaison des 5 modeles ML, distribution de la variable cible, correlation des features avec maintenance_required, distribution par profil de machine. Conformite EU AI Act affichee.

![Performance Modele IA Streamlit](docs/images/streamlit_modele_ia.png)

### 7.3 Dashboards Grafana — 3 tableaux de bord par role

Grafana, retenu en MSPR 1 comme outil de restitution principal, fournit 3 dashboards adaptes aux differents niveaux hierarchiques :

**Dashboard DG Groupe — Direction Generale**
6 KPIs en temps reel (TRS global 96.9%, Taux Maintenance 3.10%, Taux Anomalies 8.60%, Machines Actives 100, Usines 5, RUL Moyen 348 min), benchmark des 5 usines, repartition des pannes et maintenance par usine.

![Dashboard Grafana DG Groupe](docs/images/grafana_dg.png)

**Dashboard Directeur d'Usine**
Filtrable par usine (variable Grafana). 4 KPIs du site (Machines Actives 21, Taux Maintenance Site 2.30%, Temperature Moyenne 66.5 degres C, RUL Moyen Site 357 min). 3 jauges capteurs (Temperature, Vibration, Risque d'Arret) avec code couleur vert-jaune-rouge. Detail des machines avec tableau interactif. Pannes du site par type.

![Dashboard Grafana Directeur Usine](docs/images/grafana_usine.png)

**Dashboard Technicien Maintenance**
4 indicateurs d'alerte (Machines a Risque 0, RUL Critique 0, Surchauffe 0, Maintenance Requise 2). Plan d'action maintenance avec les machines critiques classees par priorite et action recommandee. Historique des pannes par type et par profil machine.

![Dashboard Grafana Technicien](docs/images/grafana_technicien.png)

### 7.4 Regles metier implementees

| Regle | Seuil | Action declenchee |
|-------|-------|-------------------|
| Temperature critique | Superieur a 100 degres C | Alerte critique, recommandation arret |
| Vibration critique | Superieur a 70 mm/s | Alerte critique, verification roulements |
| RUL critique | Inferieur a 50 min | Alerte critique, maintenance urgente |
| TRS minimum | Inferieur a 75% | Alerte production |
| Taux de rebuts | Superieur a 3% | Alerte qualite |
| Taux d'anomalies | Superieur a 10% | Investigation data team |
| Human-in-the-Loop | Toute prediction | Validation humaine obligatoire avant action |

---

## 8. Tests et validation (C5)

### 8.1 Strategie de test — Pyramide

| Niveau | Nombre de tests | Couverture cible | Frequence |
|--------|:--------------:|:---------------:|-----------|
| Tests unitaires | 100+ | Superieur ou egal a 80% du code | A chaque commit |
| Tests d'integration | 20-30 | Flux critiques | A chaque Pull Request |
| Tests de recette | 5-10 scenarios | Cas metier | Avant release |
| Tests de performance | 3-5 tests | Charge et stress | Hebdomadaire |

### 8.2 Tests implementes

**Tests de qualite des donnees** (test_data_quality.py — 14 tests)
- Structure du dataset : non vide, minimum 50 000 lignes, colonnes obligatoires presentes, colonnes enrichies presentes
- Qualite des donnees : pas de valeurs nulles sur les colonnes critiques, plages de valeurs respectees (temperature entre -10 et 200, vibration positive, RUL positive)
- Coherence metier : 50 a 100 machines, 5 usines, noms d'usines corrects, minimum 10 machines par usine, variable cible binaire, test anti-leakage machine_status, downtime_risk entre 0 et 1

**Tests des modeles ML** (test_model.py — 12 tests)
- Random Forest : chargement, prediction, prediction binaire, predict_proba, nombre de features
- XGBoost : chargement, prediction, prediction binaire
- Isolation Forest : chargement, prediction, sortie dans {-1, 1}
- RF Regressor RUL : chargement, prediction positive (11 features), prediction numerique

**Tests d'integration** (test_integration.py — 6 tests)
- Machine normale non detectee comme critique
- Machine critique correctement detectee avec alertes
- Coherence batch vs unitaire
- Detection d'anomalies sur valeurs critiques
- RUL normal superieur a RUL critique
- Workflow complet : /health, /predict, /anomaly, /predict/rul, /metrics, /model-info

### 8.3 Donnees de test

| Jeu | Temperature | Vibration | RUL | Risque | Attendu |
|-----|:---------:|:---------:|:---:|:------:|---------|
| SAMPLE_NORMAL | 75 degres C | 35 mm/s | 400 min | 0.1 | Pas d'alerte |
| SAMPLE_CRITICAL | 115 degres C | 85 mm/s | 10 min | 0.95 | Alerte critique |

### 8.4 Seuils d'acceptation

| Metrique | Seuil minimum | Seuil cible |
|----------|:------------:|:-----------:|
| Accuracy | 85% ou plus | 90% ou plus |
| Precision | 85% ou plus | 90% ou plus |
| Recall | 90% ou plus | 95% ou plus |
| F1-Score | 87% ou plus | 92% ou plus |
| MAE (RUL) | Inferieur ou egal a 24h | Inferieur ou egal a 12h |
| R-carre (RUL) | 0.80 ou plus | 0.90 ou plus |

### 8.5 Scenarios de recette metier

| Ref. | Scenario | Critere de reussite |
|------|----------|---------------------|
| REC-01 | Detection anomalie vibration | Alerte declenchee en moins de 2 min |
| REC-02 | Prediction panne a 48h | Estimation RUL entre 24 et 72h |
| REC-03 | Pas de fausse alerte en conditions normales | Zero alerte sur machine saine |
| REC-04 | Donnees capteur manquantes | Systeme degrade sans crash |
| REC-05 | Mise a jour modele sans regression | F1 stable a plus ou moins 5% |

---

## 9. Integration continue (C6)

### 9.1 Pipeline GitHub Actions

La pipeline CI/CD est implementee dans `.github/workflows/ci.yml` (146 lignes) et s'execute a chaque push ou Pull Request sur la branche main :

![Pipeline CI/CD GitHub Actions](docs/images/diag_cicd.png)

### 9.2 Detail des 3 jobs

**Job 1 — Lint (Ruff)**
- Environnement : Ubuntu, Python 3.11
- Commandes : `ruff check` (verification regles de style), `ruff format --check` (verification formatage)
- Bloquant : le job suivant ne demarre pas si le lint echoue

**Job 2 — Tests (pytest)**
- Prerequis : service PostgreSQL 15-alpine lance pour les tests d'integration
- Commandes : `pytest` avec couverture (--cov=api --cov=models)
- Rapports generes : XML (machine-readable) + HTML (human-readable)
- Artefact uploade : rapport de couverture conserve 14 jours
- Cache pip active pour accelerer l'installation

**Job 3 — Build Docker**
- Strategie matrix : construction parallele des images `api` et `dashboard`
- Docker Buildx avec cache GitHub Actions (GHA)
- Verification : `docker inspect` pour valider l'image
- Pas de push (build + validation uniquement)

---

## 10. Documentation et conformite (C7)

### 10.1 Inventaire des documents

9 documents techniques totalisant plus de 180 Ko de documentation :

| Document | Taille | Competence couverte | Contenu |
|----------|--------|--------------------|---------| 
| architecture.md | 18.5 Ko | C2 | Architecture 7 couches, comparatifs, dimensionnement |
| technical_choices.md | 24.3 Ko | C2 | Justification de chaque choix technique |
| validation_plan.md | 27.9 Ko | C5 | Pyramide de tests, scenarios de recette, matrice de tracabilite |
| deployment_plan.md | 23.4 Ko | C3/C4 | Plan 4 phases sur 12 mois, criteres Go/No-Go |
| change_management.md | 23.0 Ko | C8 | 4 axes, FutureWheel, Modele de Bridge |
| rgpd_analysis.md | 21.6 Ko | C7 | Analyse RGPD, EU AI Act, PIA |
| client_interview.md | 20.6 Ko | C1 | Entretien semi-directif, 24 questions, verbatims |
| user_guide.md | 10.8 Ko | C7 | Guide utilisateur metier (interpretation resultats, limites) |
| soutenance.md | 10.7 Ko | — | Support de soutenance (15 slides) |

### 10.2 Guide utilisateur metier

Le guide utilisateur (user_guide.md) est un document synthetique de 1 a 2 pages destine aux equipes maintenance. Il couvre :
- Ce que fait la solution (detection predictive, estimation RUL, alertes)
- Comment interpreter les resultats (niveaux de risque, categories RUL)
- Les limites et conditions d'utilisation (donnees synthetiques, Human-in-the-Loop obligatoire)
- Les actions a entreprendre selon le niveau d'alerte

### 10.3 Conformite entre realisation et cahier des charges

| Exigence du sujet MSPR 2 | Fichier/composant correspondant | Statut |
|--------------------------|-------------------------------|--------|
| Code source versionne sur Git | Repository GitHub HASHT85/MSPR2-MECHA | Conforme |
| Jeux de donnees + hypotheses | data/processed/ + data_dictionary.md | Conforme |
| Modeles ML avec metriques | models/saved_models/ + models/evaluation/ | Conforme |
| Deploiement Docker | docker-compose.yml + 2 Dockerfiles | Conforme |
| CI/CD | .github/workflows/ci.yml | Conforme |
| Solution applicative | API + Streamlit + Grafana | Conforme |
| Schema d'architecture | docs/architecture.md | Conforme |
| Choix techniques argumentes | docs/technical_choices.md | Conforme |
| RGPD | docs/rgpd_analysis.md | Conforme |
| Compte-rendu client | docs/client_interview.md | Conforme |
| Guide utilisateur | docs/user_guide.md | Conforme |
| Conduite du changement | docs/change_management.md | Conforme |
| Plan de validation | docs/validation_plan.md | Conforme |

---

## 11. Conduite du changement (C8)

### 11.1 Populations impactees

| Population | Effectif | Niveau de changement |
|-----------|----------|---------------------|
| Operateurs machines | Environ 80 personnes | Modere |
| Techniciens maintenance | Environ 30 personnes | Fort |
| Responsables maintenance | 5 personnes | Fort |
| Direction industrielle | 3 a 5 personnes | Faible |
| Equipe IT/DSI | 5 a 10 personnes | Fort |

### 11.2 Les 4 axes de la conduite du changement

**Axe 1 — Informer**
- Note de direction officielle (Semaine 1)
- Kick-off projet (Semaine 2)
- Video de presentation (3 min) : "Ce que l'IA fait et ne fait pas"
- FAQ initiale (Semaine 3)
- Messages adaptes par population (direction, techniciens, operateurs)

**Axe 2 — Communiquer**
- COPIL mensuel (direction + responsables)
- COPROJ bi-mensuel (equipe projet + DSI)
- Points usine hebdomadaires (responsable site + ambassadeurs)
- Newsletter "MECHA Predict News" mensuelle
- Gestion proactive des rumeurs (4 reponses types preparees)

**Axe 3 — Former**
Programmes de formation adaptes a chaque profil :

| Profil | Duree | Format | Contenu |
|--------|-------|--------|---------|
| Operateurs | 1h | Presentiel usine | Lire le dashboard, comprendre les alertes |
| Techniciens | 4h (2 x 2h) | Presentiel + e-learning | Interpreter les predictions, agir sur les alertes |
| Responsables | 4h (2 x 2h) | Presentiel | Piloter avec les KPIs, valider les decisions IA |
| Direction | 1h | Visioconference | Vision strategique, ROI |
| IT/DSI | 8h (2 jours) | Presentiel + TP | Administration, maintenance, troubleshooting |

Supports de formation :
- 5 tutoriels video (2 a 5 min chacun)
- Fiches reflexes plastifiees A5
- E-learning avec quiz (seuil de validation : 80% ou plus)
- Sandbox de test

**Axe 4 — Faire participer**
- 1 a 2 ambassadeurs par site (5 au total)
- 4 ateliers de co-construction
- Feedback continu : bouton in-app, boite a idees, enquetes
- Retour d'experience (REX) a chaque fin de phase

### 11.3 Modeles de reference

**FutureWheel** : Methode de cartographie des impacts en cercles concentriques, des effets directs (cercle 1 : alertes predictives, modification des routines) aux effets indirects (cercle 2 : reduction des couts, montee en competences) jusqu'aux effets lointains (cercle 3 : culture data-driven, competitivite renforcee).

**Modele transitionnel de William Bridge** : 3 phases de transition psychologique :
1. Fin de l'ancien monde : abandon de la maintenance curative pure
2. Zone neutre : cohabitation ancien/nouveau systeme, periode d'adaptation
3. Nouveau depart : adoption du systeme predictif, nouveaux reflexes

### 11.4 KPIs de suivi du changement

| Categorie | Indicateur | Objectif |
|-----------|-----------|---------|
| Adoption | Taux de connexion au dashboard | 60% puis 90% |
| Adoption | Formation completee | 100% |
| Adoption | Alertes consultees dans les 15 min | 70% puis 95% |
| Satisfaction | NPS utilisateurs | Superieur ou egal a 7 sur 10 |
| Impact metier | Arrets non planifies par mois | De 15 a 5 ou moins (-66%) |
| Impact metier | Cout maintenance | -20% |
| Impact metier | Disponibilite machines | De 88% a 95% ou plus |
| Impact metier | Delai de reaction | De 4h a 1h |

---

## 12. Conformite reglementaire — RGPD et EU AI Act

### 12.1 Cadre reglementaire

| Texte | Applicabilite |
|-------|--------------|
| RGPD (UE 2016/679) | Donnees personnelles des operateurs (emails, logs) |
| Loi Informatique et Libertes | Sites francais (Lyon, Toulouse, Nantes) |
| LOPDGDD | Sites espagnols (Barcelone, Madrid) |
| EU AI Act | Systeme de decision assiste par IA |
| Directive NIS 2 | Securite des reseaux et systemes d'information |
| IEC 62443 | Securite des systemes industriels |

### 12.2 Classification des donnees

**Donnees machine (non personnelles)** : temperature, vibration, pression, humidite, energie, identifiant machine, historique maintenance, predictions IA, alertes. Conservation : 2 ans.

**Donnees personnelles minimales** : adresses email des responsables maintenance, adresses IP dans les logs, identifiants de connexion. Conservation : 6 mois a 1 an.

### 12.3 Analyse d'impact (PIA)

- **Configuration actuelle** (donnees machine uniquement) : PIA non necessaire
- **Configuration avec donnees operateurs** (evolution future, environ 80 operateurs) : PIA obligatoire

Risques identifies dans le scenario avec donnees operateurs :

| Risque | Niveau |
|--------|--------|
| Surveillance percue des operateurs | Critique |
| Discrimination basee sur correlations IA | Critique |
| Utilisation des donnees pour sanctions | Critique |
| Acces non autorise | Significatif |
| Profilage involontaire | Significatif |

### 12.4 Classification EU AI Act

Le systeme MECHA Predict est classe en **risque limite** selon le reglement europeen sur l'intelligence artificielle. Les obligations de transparence sont respectees :

| Obligation | Implementation |
|-----------|---------------|
| Documentation du modele | Model Cards pour les 5 modeles |
| Donnees d'entrainement documentees | Dictionnaire de donnees, hypotheses, limites |
| Limites et biais documentes | 4 types de biais identifies par modele |
| Human-in-the-Loop | Mention explicite dans le dashboard et l'API : toute prediction doit etre validee par un operateur qualifie |
| Transparence | L'IA fournit des recommandations, pas des decisions |

### 12.5 Mesures techniques de securite

- Chiffrement TLS 1.3 (donnees en transit), AES-256 (donnees au repos)
- Controle d'acces RBAC avec 6 roles definis
- Authentification API par cle (header X-API-Key)
- Journalisation des acces
- Variables sensibles dans .env (hors du code source)
- .env dans .gitignore, .env.example fourni

---

## 13. Plan de deploiement multi-sites

### 13.1 Architecture de deploiement centralisee

L'architecture retenue est centralisee, avec un serveur principal a Lyon (siege) et des passerelles edge par site :

![Architecture de deploiement centralisee](docs/images/diag_deployment.png)

### 13.2 Deploiement progressif en 4 phases

| Phase | Periode | Sites | Machines | Objectif |
|-------|---------|-------|----------|---------|
| Phase 1 — Pilote | Juin-Aout 2026 | Lyon | 10 | Valider en conditions reelles |
| Phase 2 — France | Sept-Nov 2026 | Toulouse + Nantes | 30 (cumul) | Deployer les sites francais |
| Phase 3 — Espagne | Dec 2026-Fev 2027 | Barcelone + Madrid | 50 (cumul) | Adaptation i18n, extension |
| Phase 4 — Stabilisation | Fev-Mai 2027 | Tous | 50 | Optimisation, formation continue |

### 13.3 Criteres Go/No-Go par phase

| Critere | Poids | Seuil minimum |
|---------|:-----:|:-------------:|
| Infrastructure operationnelle | 20% | 100% |
| Donnees capteurs disponibles | 20% | 95% ou plus |
| Accuracy modele | 20% | 80% ou plus |
| Fausses alertes | 15% | 15% ou moins |
| Adoption utilisateurs | 15% | 60% ou plus |
| Satisfaction utilisateurs | 10% | 6 sur 10 ou plus |

### 13.4 Plan de rollback

Criteres de declenchement du retour arriere :
- Perte de donnees superieure a 30% pendant plus d'1 heure
- Plus de 5 fausses alertes critiques en 24 heures
- Indisponibilite API superieure a 2 heures
- Impact negatif mesurable sur la production
- Rejet par plus de 50% des utilisateurs

### 13.5 Regles de notification

| Severite | Canaux | Delai |
|----------|--------|-------|
| Information | Dashboard uniquement | 1 heure |
| Avertissement | Email + Dashboard | 15 minutes |
| Critique | SMS + Email + Dashboard | 5 minutes |

---

## 14. Bilan et perspectives

### 14.1 Bilan quantitatif du projet

| Metrique | Valeur |
|----------|--------|
| Lignes de code total | Environ 4 630 lignes |
| Fichiers du projet | Environ 75 fichiers |
| Taille du dataset | 110 000 enregistrements, 30 colonnes |
| Modeles ML entraines | 5 modeles |
| Endpoints API | 9 routes REST |
| Vues Streamlit | 5 pages metier |
| Dashboards Grafana | 3 par role |
| Tests automatises | 38+ tests (14 donnees + 12 modeles + 6 integration + tests API) |
| Documents techniques | 9 documents, 180+ Ko |
| Services Docker | 4 conteneurs |
| Pipeline CI/CD | 3 jobs (lint, test, build) |
| Competences couvertes | 8 sur 8 (C1 a C8) |

### 14.2 Couverture des competences

| Competence | Description | Preuve |
|------------|------------|--------|
| C1 | Collecter les besoins metiers | client_interview.md — Entretien 2h30, 24 questions, 10 besoins fonctionnels |
| C2 | Concevoir une architecture applicative | architecture.md + technical_choices.md — 7 couches, 10 comparatifs |
| C3 | Developper une application | API FastAPI (1 157 lignes) + Dashboard Streamlit (918 lignes) + Pipeline ML (887 lignes) |
| C4 | Developper une solution integree | 9 endpoints API + 5 vues Streamlit + 3 dashboards Grafana + regles metier |
| C5 | Effectuer les tests | validation_plan.md + 38 tests implementes + 5 scenarios de recette |
| C6 | Appliquer l'integration continue | .github/workflows/ci.yml — 3 jobs sequentiels |
| C7 | Verifier conformite et documenter | 9 documents + guide utilisateur + conformite cahier des charges |
| C8 | Conduire le changement | change_management.md — 4 axes, FutureWheel, Bridge, KPIs |

### 14.3 Limites identifiees

| Limite | Impact | Plan de remediation |
|--------|--------|---------------------|
| Donnees synthetiques | Performances reelles peuvent differer | Reevaluation avec donnees de production |
| Recall a 62% | 38% des pannes non detectees | Optimisation du seuil, enrichissement features |
| R-carre RUL a 59.8% | Precision limitee de l'estimation du temps avant panne | Ajout de features temporelles, modele LSTM |
| Pas de deep learning | Potentiellement moins performant sur les sequences longues | LSTM prevu si donnees suffisantes (plus de 2 ans d'historique) |
| Base centralisee | Point unique de defaillance | Backup quotidien, buffer local par site |
| Streamlit = prototypage | Interface moins professionnelle qu'une application custom | Suffisant pour la V1, refonte React possible en V2 |

### 14.4 Perspectives d'evolution

| Horizon | Evolution | Condition de declenchement |
|---------|-----------|---------------------------|
| Court terme (6 mois) | TimescaleDB pour series temporelles | Volume superieur a 10 Go par mois |
| Court terme (6 mois) | Redis pour cache des predictions | Latence API superieure a 500 ms |
| Moyen terme (12 mois) | MLflow pour versioning des modeles | Plus de 3 modeles en production |
| Moyen terme (12 mois) | Apache Kafka pour streaming | Plus de 100 machines |
| Long terme (18+ mois) | LSTM / Transformer pour deep learning | Plus de 2 ans d'historique, plus de 100 machines |
| Long terme (18+ mois) | Kubernetes pour orchestration | Plus de 10 sites ou microservices |

### 14.5 ROI projete

| Poste | Estimation annuelle |
|-------|:-------------------:|
| Reduction des arrets non planifies (-25%) | 150 000 a 250 000 euros |
| Optimisation du stock de pieces (-30%) | 30 000 a 60 000 euros |
| Reduction des penalites contractuelles | 50 000 a 100 000 euros |
| Reduction de la consommation energetique | 20 000 a 40 000 euros |
| **Total economies** | **200 000 a 300 000 euros par an** |
| Investissement initial | 150 000 euros |
| **Retour sur investissement** | **Inferieur a 12 mois** |

---

## 15. Annexes

### 15.1 Inventaire complet des fichiers

| Composant | Fichiers | Volume |
|-----------|----------|--------|
| API FastAPI | api/main.py, api/Dockerfile | 1 157 lignes |
| Dashboard Streamlit | app/src/dashboard.py, app/Dockerfile | 918 lignes |
| Scripts data | generate_data.py, merge_datasets.py | 931 lignes |
| Pipeline ML | train_models.py | 887 lignes |
| Schema BDD | db/init.sql, db/load_data.sh | 123 lignes |
| Tests | 3 fichiers (data, modeles, integration) | 432 lignes |
| CI/CD | .github/workflows/ci.yml | 146 lignes |
| Docker | docker-compose.yml | 159 lignes |
| Documentation | 9 fichiers | 180+ Ko |
| Grafana | 3 dashboards JSON + 2 provisioning | 5 fichiers |
| Modeles | 5 .joblib + 5 model cards + 6 metriques | 21 fichiers |

### 15.2 Stack technique complete

| Couche | Technologies |
|--------|-------------|
| Langage | Python 3.11 |
| ML | scikit-learn, XGBoost, pandas, NumPy, joblib |
| API | FastAPI, Pydantic, uvicorn |
| Dashboard | Streamlit, Plotly, requests |
| Monitoring | Grafana OSS |
| BDD | PostgreSQL 16 Alpine |
| Conteneurisation | Docker, Docker Compose |
| CI/CD | GitHub Actions, Ruff, pytest, pytest-cov |
| Versionning | Git, GitHub |

### 15.3 Captures d'ecran

Tendance de temperature par machine sur 3 jours, avec seuil critique a 100 degres C :

![Tendance Temperature par Machine](docs/images/streamlit_temperature.png)

### 15.4 References bibliographiques

- EU AI Act — Reglement (UE) 2024/1689 du Parlement europeen
- RGPD — Reglement (UE) 2016/679 du Parlement europeen
- EN 9100 — Systemes de management de la qualite aeronautique
- IATF 16949 — Systemes de management de la qualite automobile
- IEC 62443 — Securite des systemes d'automatisation industrielle
- Directive NIS 2 (UE) 2022/2555 — Securite des reseaux et systemes d'information
- scikit-learn Documentation — https://scikit-learn.org
- XGBoost Documentation — https://xgboost.readthedocs.io
- AI4I 2020 Predictive Maintenance Dataset — UCI Machine Learning Repository

---

> **Document valide par** : Equipe projet MECHA  
> **Date de validation** : Mai 2026  
> **Repository** : https://github.com/HASHT85/MSPR2-MECHA
