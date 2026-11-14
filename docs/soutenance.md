# Support et Conducteur de Soutenance Orale — MSPR 2 MECHA Predict

> **Certification** : RNCP35584 (Niveau 7) — Expert en Informatique et Système d'Information (EPSI)  
> **Épreuve** : MSPR **TPRE841** — Bloc 4 : *Concevoir et développer des solutions applicatives métier et spécifiques* (`C1` à `C8`)  
> **Format officiel** : **20 minutes de présentation en équipe** + **30 minutes d'échanges individuels et collectifs avec le jury**  
> **Équipe (maîtrise croisée intégrale C1–C8)** : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel  
> **Fichiers diaporama associés** : `livrables/03_Support_Soutenance/Support_Soutenance_MECHA_TPRE841.pptx` & `.pdf` (18 slides 16:9)

---

## Répartition Chronométrée des 20 Minutes (4 × 5 min)

> **Règle d'or évaluation individuelle** : chaque membre présente un bloc cohérent de **5 minutes** mais maîtrise l'intégralité des 8 compétences (`C1`–`C8`), les modélisations **BPMN 2.0** et les **3 extraits de code clés** pour répondre individuellement aux questions du jury durant les 30 minutes d'échange.

| Séquence | Intervenant proposé | Durée | Slides | Compétences démontrées |
|----------|---------------------|:-----:|:------:|------------------------|
| **Partie 1** | **Malek El Fayedh** | `00:00 – 05:00` | Slides 1 à 5 | Contexte industriel, continuité **TPRE831 -> TPRE841**, recueil besoins **C1**, processus actuel **BPMN 2.0 AS-IS**, architecture 7 couches & NTP **C2** |
| **Partie 2** | **Thibaut Doreau** | `05:00 – 10:00` | Slides 6 à 9 | Pipeline données hybrides publiques (110k) & modèle SQL **C2/C3**, anti-fuite & 5 modèles ML **C3**, analyse **AMDEC**, **Extrait de code #1** |
| **Partie 3** | **Vincent Gonçalves** | `10:00 – 14:45` | Slides 10 à 13 | Solution intégrée **C4** (API 9 routes, formalisme YAML/JSON/SQL), **Extraits de code #2 & #3**, interfaces Streamlit (6 vues) & Grafana (3 vues), tests **C5** (104 PASS) & CI/CD **C6** |
| **Partie 4** | **Pierre-Louis Guinel** | `14:45 – 20:00` | Slides 14 à 18 | Conformité & guide métier 2 pages **C7**, conduite du changement & outil in-app **C8**, processus cible **BPMN 2.0 TO-BE**, RGPD / EU AI Act, déploiement multi-sites, audit IA générative & ROI |

---

## Détail Slide par Slide (18 Slides)

### Slide 1 — Titre, Continuité & Chiffres Clés (`00:00 – 01:00`)
- **MECHA Predict** : Plateforme industrielle de maintenance prédictive par IA (5 usines FR/ES, 50 machines MECHA).
- Continuité directe de **MSPR TPRE831** (cadrage & PoC) vers **MSPR TPRE841** (solution applicative intégrée, conteneurisée et validée C1–C8).
- 4 indicateurs synthétiques : `5 Usines`, `110 000` mesures capteurs, `90,0 %` de rappel détection (`F1 = 80,4 %`), `104 / 104` tests Pytest en CI/CD.

### Slide 2 — Problématique Industrielle & Enjeux Métiers (`01:00 – 02:00`)
- **5 sites** : Lyon (siège), Toulouse, Nantes (60 % Aéronautique EN 9100) + Barcelone, Madrid (40 % Automobile IATF 16949).
- **Douleur métier** : 70 % de maintenance curative subie, données silotées (SCADA / MES / ERP), 12 à 18 arrêts non planifiés/mois, **2,4 M EUR/an** de budget maintenance et **180 k EUR** de pénalités contractuelles.
- **Cibles** : disponibilité `>= 95 %` (vs 87 %), arrêts `< 4 h/mois`, économies projetées **200 à 300 k EUR/an** (**ROI < 12 mois**).

### Slide 3 — Collecte et Formalisation sans Biais des Besoins — Compétence C1 (`02:00 – 03:00`)
- Entretien semi-directif structuré (2h30, 6 axes A–F, 24 questions) avec M. Duval (Directeur Industriel) et Mme Martin (Resp. Maintenance Lyon).
- Méthode de transcription en 4 étapes : *1. Verbatims bruts -> 2. Qualification des Pain Points -> 3. Priorisation MoSCoW (10 BF) -> 4. Exigences mesurables & recette (7 BNF)*.
- Livrable : `livrables/02_Documentation_et_Validation/01_Entretien_Client_Besoins_C1.pdf`.

### Slide 4 — Modélisation du Processus Actuel — BPMN 2.0 AS-IS (`03:00 – 03:50`)
- Schéma normalisé OMG BPMN 2.0 (`docs/bpmn/01_mecha_maintenance_AS_IS.bpmn` / `diag_bpmn_asis.png`) sur 3 couloirs métiers (*Opérateur Ligne, Resp. Production, Tech. Maintenance*).
- Mise en évidence des goulets d'étranglement : 80 % des casses sans signe avant-coureur perçu à temps, immobilisation de 4 à 16 h (3 500 à 8 000 EUR/h), saisie papier/Excel non partagée inter-sites.

### Slide 5 — Architecture Applicative en 7 Couches & Critères C2 (`03:50 – 05:00`)
- Acquisition **IoT + SCADA + MES** synchronisés en **UTC via NTP**, stockage **PostgreSQL 15**, 5 modèles ML, API **FastAPI** (9 routes), **Streamlit (6 vues)** + **Grafana (3 dashboards)** (`diag_architecture.png`).
- Justification formelle des 4 propriétés C2 : **Stabilité**, **Efficacité** (< 25 ms), **Pérennité** (découplage REST, open-source) et **Tolérance aux pannes** (triple fallback + buffer Edge SQLite 72 h).

### Slide 6 — Ingénierie des Données (110 000 lignes) & Modèle Physique SQL (`05:00 – 06:15`)
- **100 000 mesures simulées MECHA** + **10 000 mesures publiques communautaires UCI AI4I 2020** (*CC BY 4.0*, zéro donnée confidentielle réelle conformément à la p.4 du sujet).
- **6 features temporelles glissantes** + typage entier strict (`Int64`) garantissant l'ingestion directe `\COPY` PostgreSQL sans flottants parasites.
- Modèle physique `db/init.sql` (`diag_database.png`) : 4 tables relationnelles, vue temps réel `v_machine_status` et 11 index B-Tree.

### Slide 7 — Modélisation sans Fuite & Performances IA — Compétence C3 (`06:15 – 07:30`)
- Exclusion stricte de `machine_status`, `predicted_remaining_life` et `downtime_risk` + **split temporel 80/20 stratifié par source** (`88 000` train / `22 000` test).
- **Random Forest** (principal) : **F1 = 80,4 %**, **Rappel = 90,0 %**, **AUC = 0,988** | **XGBoost** (secours) : **F1 = 81,1 %** | **RF Regressor RUL** : **MAE = 26,9 min** (`R² = 0,719`) | **Isolation Forest** : **AUC = 0,839**.
- Vue réelle `streamlit_modele_ia.png` + transparence scientifique par source (F1 = 82,2 % sur simulé vs 7,3 % sur UCI AI4I).

### Slide 8 — Analyse AMDEC — Équipements & Système IA (`07:30 – 08:30`)
- 5 modes de défaillance analysés (`diag_amdec.png`) : *Surchauffe* (`60 -> 24`), *Vibration roulements* (`48 -> 24`), *Chute de pression* (`36 -> 18`), *Usure outil* (`24 -> 8`), *Défaut électrique* (`20 -> 12`) -> **-50 % de criticité moyenne**.
- AMDEC de second niveau sur le système IA : mitigation des faux négatifs (Rappel 90 % + Isolation Forest) et filtrage des faux positifs (*Human-in-the-Loop*).

### Slide 9 — Extrait de Code #1 — Anti-Fuite & Split Temporel (`08:30 – 10:00`)
- Extrait `models/training/train_models.py` : verrouillage de `LEAKY_FEATURES`, contrat des 10 `FEATURES` capteurs et boucle `df.groupby("data_source")` garantissant un split chronologique 80/20 honnête sur chaque source.

### Slide 10 — Solution Applicative Intégrée & Formalisme Déclaratif — Compétence C4 (`10:00 – 11:00`)
- **API FastAPI (`api/main.py`)** : 9 routes REST, schémas Pydantic bornés (HTTP 422), authentification `X-API-Key`, conteneur non-root `appuser` et volumes `:ro`.
- **4 formalismes déclaratifs C4** : provisioning YAML Grafana, dashboards JSON + vue SQL `v_machine_status`, seuils métiers à chaud (`GET/PUT /alerts/config`) et règles de transformation centralisées.

### Slide 11 — Extraits de Code #2 & #3 — Résilience & Paramétrage (`11:00 – 12:00`)
- **Extrait #2 (`api/main.py`)** : chaîne de triple fallback (`Random Forest -> XGBoost -> _mock_predict`) garantissant zéro erreur HTTP 500 en usine.
- **Extrait #3 (`app/src/dashboard.py`)** : mise à jour dynamique à chaud des seuils critiques via `api_put("/alerts/config", ...)` depuis l'interface métier.

### Slide 12 — Interfaces Métiers — Streamlit (6 Vues) & Grafana (3 Vues) (`12:00 – 13:15`)
- Captures couplées `dashboard_streamlit.png` et `grafana_dg.png` : complémentarité entre l'application d'aide à la décision IA (**Streamlit**, 6 vues dont `Accompagnement`) et la supervision SQL temps réel (**Grafana**, 3 profils).

### Slide 13 — Tests Automatisés (104 PASS) & Pipeline CI/CD — Compétences C5 & C6 (`13:15 – 14:45`)
- **104 tests Pytest (`100 % PASS`, `0 skipped`)** : 21 Data/SQL, 16 ML, 61 API (87 % couverture), 6 Intégration + plan de correction `CORR-01..05`.
- Schéma `diag_cicd.png` : pipeline GitHub Actions bloquant en 3 jobs (*Ruff -> Régénération 110k + 5 modèles + Pytest -> Buildx Docker*).

### Slide 14 — Conformité Fonctionnelle & Guide Utilisateur Métier — Compétence C7 (`14:45 – 15:45`)
- Matrice de conformité validant 100 % du cahier des charges TPRE841 + capture `streamlit_site.png`.
- **Guide utilisateur métier strictement en 2 pages A4** (`07_Guide_Utilisateur_Metier_2pages_C7.pdf`) rédigé sans jargon data (codes couleurs, procédure en 4 étapes, limites RUL ±27 min).

### Slide 15 — Conduite du Changement & Outil Logiciel Dédié — Compétence C8 (`15:45 – 17:00`)
- Démarche en **4 axes** (*Informer, Communiquer, Former, Faire participer*) appuyée sur la **Future Wheel** et le modèle de **William Bridges**.
- Capture réelle `streamlit_accompagnement.png` : 6e vue Streamlit dédiée à la qualification terrain anonyme en 15 s, aux fiches réflexes et au calibrage des seuils C4.

### Slide 16 — Processus Cible Assisté par IA — BPMN 2.0 TO-BE (`17:00 – 17:50`)
- Schéma normalisé OMG BPMN 2.0 (`docs/bpmn/02_mecha_maintenance_TO_BE.bpmn` / `diag_bpmn_tobe.png`) illustrant le cycle prédictif 1 min, la passerelle obligatoire *Human-in-the-Loop* (EU AI Act Art. 14) et la réduction de 35 à 50 % des arrêts imprévus.

### Slide 17 — Conformité Réglementaire & Déploiement Multi-Sites (`17:50 – 19:00`)
- **RGPD & LOPDGDD** (zéro donnée nominative opérateur, PIA conditionnel) + **EU AI Act 2024/1689** (risque limité, 5 Model Cards, Art. 14).
- Trajectoire 12 mois en 4 phases (Lyon -> Toulouse/Nantes -> Barcelone/Madrid i18n ES -> Stabilisation Go/No-Go & Rollback < 15 min) + schéma réseau `diag_deployment.png` (VLAN IEC 62443, VPN WireGuard, buffer Edge 72 h).

### Slide 18 — Bilan des Livrables, Audit de l'IA Générative & ROI (`19:00 – 20:00`)
- **100 % des livrables vérifiés** dans `livrables/` + scripts de démonstration locale 1 clic (`scripts/start_demo.*`).
- **Usage raisonné & audité de l'IA générative** : traçabilité complète des prompts et de leur correction critique par l'équipe en **Section 15.3** du rapport global (data leakage, typage SQL `Int64`).
- **Impact ROI** : **200 à 300 k EUR/an** d'économies projetées pour **150 k EUR** d'investissement initial (**retour < 12 mois**) -> ouverture de la démonstration live puis des 30 minutes d'échanges.
