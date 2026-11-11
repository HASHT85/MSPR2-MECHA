# Dictionnaire de Données — MECHA Dataset Hybride (MSPR 2 — TPRE841)

> **Version** : 3.1 | **Date** : Mai 2026 | **Auteur** : Équipe MECHA  
> **Sources** : Dataset MECHA simulé (100 000 lignes) + Jeu public communautaire de référence AI4I 2020 Predictive Maintenance (10 000 lignes, UCI ML Repository / Kaggle — aucune donnée industrielle confidentielle privée conformément au cahier des charges p.4)

## 1. Vue d'ensemble

| Propriété | Valeur |
|-----------|--------|
| Nombre d'enregistrements | **110 000** (100 000 simulés + 10 000 publics AI4I 2020) |
| Nombre de colonnes | **30** |
| Machines couvertes | **100 identifiants** (IDs 1–50 parc simulé MECHA + IDs 51–100 benchmark public AI4I) |
| Usines MECHA | **5 sites** (3 en France : Lyon, Toulouse, Nantes ; 2 en Espagne : Barcelone, Madrid) |
| Granularité temporelle | 1 mesure par minute et par machine |
| Taille fichier exploitable | ~20 Mo (`data/processed/mecha_dataset_processed.csv`) |
| Taille fichier brut avant fusion | ~16 Mo (`data/raw/mecha_dataset_raw.csv`) + `data/external/ai4i_2020_real.csv` |

### Composition par source de données

| Source (`data_source`) | Enregistrements | Période | Nature et conformité |
|------------------------|-----------------|---------|----------------------|
| `MECHA_simulated` | 100 000 | Janvier 2025 | Séries temporelles IoT simulées reproduisant la dégradation progressive de 50 machines sur 5 usines FR/ES |
| `AI4I_2020_real` | 10 000 | Mars 2025 | Jeu de données public communautaire *AI4I 2020 Predictive Maintenance* (UCI Machine Learning Repository, licence CC BY 4.0) harmonisé au schéma MECHA |

> **Conformité confidentialité industrielle (Cahier des charges Section III, p.4)** : Aucune donnée industrielle privée ou confidentielle n'est utilisée. Le corpus combine exclusivement une simulation métier Python reproductible (`seed=42`) et un jeu ouvert académique de référence (UCI / Kaggle).

---

## 2. Description exhaustive des 30 colonnes

### 2.1 Colonnes d'identification et de contexte industriel (9 colonnes)

| # | Colonne | Type SQL / Python | Description | Valeurs / Plage | Origine |
|:-:|---------|-------------------|-------------|-----------------|---------|
| 1 | `timestamp` | `TIMESTAMP` / `datetime` | Horodatage synchronisé (UTC/NTP) de la mesure | Janvier – Mars 2025 | Toutes sources |
| 2 | `machine_id` | `INTEGER` / `Int64` | Identifiant unique de l'équipement | `1`–`50` (MECHA simulé), `51`–`100` (AI4I public) | Toutes sources |
| 3 | `usine_id` | `VARCHAR(20)` / `str` | Code du site industriel MECHA | `USN-FR-01` à `USN-FR-03`, `USN-ES-01`, `USN-ES-02` | Enrichissement MSPR 2 |
| 4 | `usine_nom` | `VARCHAR(50)` / `str` | Ville d'implantation de l'usine | `Lyon`, `Toulouse`, `Nantes`, `Barcelone`, `Madrid` | Enrichissement MSPR 2 |
| 5 | `usine_pays` | `VARCHAR(20)` / `str` | Pays d'implantation | `France`, `Espagne` | Enrichissement MSPR 2 |
| 6 | `ligne_production` | `VARCHAR(10)` / `str` | Ligne d'atelier automatisée (MES) | `LP-A`, `LP-B`, `LP-C` | Enrichissement MSPR 2 |
| 7 | `type_piece` | `VARCHAR(50)` / `str` | Référence fonctionnelle usinée | `Arbre_moteur`, `Disque_frein`, `Carter_boite`, `Pale_turbine`, `Axe_roue` | Enrichissement MSPR 2 |
| 8 | `machine_profile` | `VARCHAR(20)` / `str` | Profil structurel de fiabilité machine | `robuste`, `standard`, `fragile`, `vieillissante` | Toutes sources |
| 9 | `data_source` | `VARCHAR(30)` / `str` | Origine de l'enregistrement (traçabilité ETL) | `MECHA_simulated`, `AI4I_2020_real` | Traçabilité MSPR 2 |

### 2.2 Mesures brutes des capteurs IoT (5 colonnes — Features ML n°1 à 5)

| # | Colonne | Type | Unité | Description | Plage nominale / observée | Rôle ML |
|:-:|---------|------|-------|-------------|---------------------------|---------|
| 10 | `temperature` | `FLOAT` | °C | Température capteur broche / bâti machine | `25.0` – `125.0` °C | Feature ML #1 (corrélation forte) |
| 11 | `vibration` | `FLOAT` | mm/s | Vitesse vibratoire efficace (RMS) | `0.0` – `120.0` mm/s | Feature ML #2 (corrélation modérée) |
| 12 | `humidity` | `FLOAT` | % | Humidité relative ambiante atelier | `30.0` – `80.0` % | Feature ML #3 (bruit environnemental) |
| 13 | `pressure` | `FLOAT` | bar | Pression du circuit hydraulique / pneumatique | `0.5` – `5.0` bar | Feature ML #4 |
| 14 | `energy_consumption` | `FLOAT` | kWh | Consommation énergétique instantanée | `0.3` – `7.0` kWh | Feature ML #5 |

### 2.3 Features temporelles dérivées (5 colonnes — Features ML n°6 à 10)

| # | Colonne | Type | Fenêtre | Formule / Signification métier | Rôle ML |
|:-:|---------|------|---------|--------------------------------|---------|
| 15 | `temp_rolling_10min` | `FLOAT` | 10 min | Moyenne glissante de `temperature` sur 10 mesures (lissage du bruit capteur) | Feature ML #6 |
| 16 | `temp_trend_1h` | `FLOAT` | 60 min | Pente linéaire de température sur 1h (détection d'emballement thermique) | Feature ML #7 |
| 17 | `vibr_rolling_10min` | `FLOAT` | 10 min | Moyenne glissante de `vibration` sur 10 mesures | Feature ML #8 |
| 18 | `temp_std_30min` | `FLOAT` | 30 min | Écart-type de `temperature` sur 30 min (instabilité thermique) | Feature ML #9 |
| 19 | `energy_vibr_ratio` | `FLOAT` | Instantané | Ratio `energy_consumption / max(vibration, 0.1)` (rendement électromécanique) | Feature ML #10 |

### 2.4 Colonnes d'état machine, cibles ML et score métier (7 colonnes)

| # | Colonne | Type | Valeurs / Plage | Usage et règles strictes anti-fuite (*Data Leakage*) |
|:-:|---------|------|-----------------|------------------------------------------------------|
| 20 | `machine_status` | `INTEGER` | `0` = Arrêt planifié, `1` = Production, `2` = Panne | Supervision SCADA/Grafana uniquement — **EXCLUE des features ML** (fuite directe de l'état de panne) |
| 21 | `anomaly_flag` | `INTEGER` | `0` = Normal, `1` = Anomalie seuil | Indicateur métier de pré-alerte capteur |
| 22 | `predicted_remaining_life` | `INTEGER` | `0` – `500` min | **Variable cible du modèle RUL** (`RandomForestRegressor`) — **EXCLUE des features de classification** |
| 23 | `failure_type` | `VARCHAR(30)` | `Normal`, `Overheating`, `Vibration_Issue`, `Pressure_Drop`, `Electrical_Fault`, `Tool_Wear_Failure`, `Random_Failure` | Typologie AMDEC de défaillance pour diagnostic |
| 24 | `maintenance_required` | `INTEGER` | `0` = Non (~95,3 %), `1` = Oui (~4,7 % en test) | **Variable cible principale de classification binaire** |
| 25 | `maintenance_type` | `VARCHAR(20)` | `none`, `preventive`, `corrective`, `recommended` | Catégorie d'intervention GMAO |
| 26 | `downtime_risk` | `FLOAT` | `0.0` – `1.0` | Score synthétique d'affichage `0.30*temp_risk + 0.25*vibr_risk + 0.45*rul_risk` — **EXCLU des features ML** |

### 2.5 Colonnes complémentaires issues du benchmark public AI4I 2020 (4 colonnes)

| # | Colonne | Type SQL / Pandas | Unité | Description | Plage observée | Disponibilité |
|:-:|---------|-------------------|-------|-------------|----------------|---------------|
| 27 | `torque_nm` | `FLOAT` / `float64` | Nm | Couple mécanique broche | `3.8` – `76.6` Nm | Renseignée sur AI4I (`NULL` sur simulé) |
| 28 | `rotational_speed_rpm` | `INTEGER` / `Int64` | tr/min | Vitesse de rotation de broche | `1168` – `2886` rpm | Renseignée sur AI4I (`NULL` sur simulé) |
| 29 | `tool_wear_min` | `INTEGER` / `Int64` | min | Durée d'usure cumulée de l'outil coupant | `0` – `253` min | Renseignée sur AI4I (`NULL` sur simulé) |
| 30 | `product_quality` | `VARCHAR(5)` / `str` | — | Gamme de qualité pièce (`L` Low, `M` Medium, `H` High) | `L`, `M`, `H` | Renseignée sur AI4I (`NULL` sur simulé) |

---

## 3. Référentiel des usines et profils machines

### 3.1 Répartition des 5 sites industriels MECHA

| Code usine | Site | Pays | Parc simulé | Spécificité industrielle |
|------------|------|------|:-----------:|--------------------------|
| `USN-FR-01` | MECHA Lyon | France | Machines 1 à 10 (10) | Site historique et pilote Industrie 4.0 |
| `USN-FR-02` | MECHA Toulouse | France | Machines 11 à 20 (10) | Pôle aéronautique haute précision |
| `USN-FR-03` | MECHA Nantes | France | Machines 21 à 30 (10) | Usinage structures et sous-ensembles |
| `USN-ES-01` | MECHA Barcelone | Espagne | Machines 31 à 40 (10) | Grande série automobile |
| `USN-ES-02` | MECHA Madrid | Espagne | Machines 41 à 50 (10) | Site polyvalent récent |

### 3.2 Profils d'hétérogénéité du parc machines

| Profil | Machines concernées | Température nominale | Vibration nominale | Prob. panne | Description |
|--------|---------------------|:--------------------:|:------------------:|:-----------:|-------------|
| `robuste` | 1, 10, 20, 30, 40, 50 (6 machines) | 70 °C | 35 mm/s | 2 % | Centres d'usinage récents |
| `standard` | 32 machines | 75 °C | 40 mm/s | 4 % | Cœur de flotte MECHA |
| `fragile` | 3, 8, 15, 22, 32, 41, 48 (7 machines) | 82 °C | 50 mm/s | 8 % | Machines fortement sollicitées |
| `vieillissante` | 5, 12, 24, 37, 43 (5 machines) | 85 °C | 55 mm/s | 10 % | Équipements anciens sous surveillance renforcée |

### 3.3 Harmonisation des modes de défaillance AI4I 2020 vers MECHA

| Code AI4I 2020 | Libellé harmonisé MECHA | Phénomène physique |
|----------------|-------------------------|--------------------|
| `TWF` (*Tool Wear Failure*) | `Tool_Wear_Failure` | Usure critique de l'outil de coupe (200–240 min) |
| `HDF` (*Heat Dissipation Failure*) | `Overheating` | Défaut de dissipation thermique |
| `PWF` (*Power Failure*) | `Electrical_Fault` | Puissance mécanique hors plage nominale |
| `OSF` (*Overstrain Failure*) | `Vibration_Issue` | Surcharge couple × usure générant des vibrations |
| `RNF` (*Random Failure*) | `Random_Failure` | Défaillance stochastique non anticipable (~0,1 %) |

---

## 4. Hypothèses de simulation et limites connues

### 4.1 Hypothèses métier retenues (`generate_data.py` & `merge_datasets.py`)
1. **Plage de production** : fonctionnement nominal de 06h00 à 22h00 et arrêt planifié nocturne (`machine_status = 0`).
2. **Dégradation continue** : accumulation progressive d'usure en fonctionnement, amplifiée par le profil de fragilité machine, entraînant une hausse corrélée de la température (+40 °C max) et de la vibration (+30 mm/s max) avec bruit gaussien capteur.
3. **Interventions** : remise à zéro de la dégradation après maintenance corrective (30–120 min) ou préventive.
4. **Conversion physique AI4I** : conversion des températures Kelvin en degrés Celsius (`T_°C = T_K - 273.15`) et typage strict en entiers nullables (`Int64`) des colonnes `rotational_speed_rpm` et `tool_wear_min` pour garantir l'import transactionnel PostgreSQL `\COPY`.

### 4.2 Limites documentées
- **Écart de domaine simulé vs AI4I public** : pour entraîner un modèle unique sur les deux sources sans valeurs manquantes, seules les **10 features capteurs communes** sont utilisées. Or dans AI4I 2020, les pannes `TWF`/`OSF`/`PWF` dépendent fortement de `torque_nm` et `tool_wear_min` (absents de la simulation), ce qui explique la performance plus basse observée isolément sur le sous-ensemble AI4I (`F1 ≈ 0,07`) contre `F1 ≈ 0,82–0,83` sur le parc simulé MECHA.
- **Déséquilibre des classes** (~95–97 % de mesures normales contre ~3–5 % nécessitant maintenance), traité par `class_weight='balanced'` et `scale_pos_weight`.
- **Absence volontaire de données personnelles** : aucun identifiant opérateur nominatif n'est présent (conformité RGPD *Privacy by Design*).
