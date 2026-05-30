# Dictionnaire de Données — MECHA Dataset Hybride (MSPR 2)

> **Version** : 3.0 | **Date** : Mai 2026 | **Auteur** : Équipe MECHA  
> **Sources** : Dataset MECHA simulé (100k lignes) + AI4I 2020 Predictive Maintenance (10k lignes, UCI ML Repository)

## Vue d'ensemble

| Propriété | Valeur |
|-----------|--------|
| Nombre d'enregistrements | ~110 000 |
| Nombre de colonnes | 29 |
| Machines couvertes | ~100 (IDs 1-50 simulées + 51-100 réelles) |
| Usines | 5 (3 France, 2 Espagne) |
| Sources de données | 2 (MECHA simulé + AI4I 2020 réel) |
| Taille fichier | ~20 Mo (CSV) |

### Composition du dataset

| Source | Enregistrements | Période | Description |
|--------|----------------|---------|-------------|
| **MECHA simulé** | ~100 000 | Jan 2025 (3 jours) | Données capteurs IoT simulées avec dégradation progressive |
| **AI4I 2020 réel** | ~10 000 | Mars 2025 | Données réelles de machines-outils industrielles (UCI ML Repository) |

> Le dataset AI4I 2020 est un **jeu de données de référence** publié par le UCI Machine Learning Repository,
> utilisé dans la littérature académique pour la maintenance prédictive. Il apporte des features
> complémentaires (couple, vitesse de rotation, usure outil) et des types de pannes réels.

## Description des colonnes

### Colonnes d'identification

| Colonne | Type | Description | Valeurs / Plage | Origine |
|---------|------|-------------|-----------------|---------|\
| `timestamp` | datetime | Horodatage de la mesure | Jan-Mars 2025 | Toutes sources |
| `machine_id` | int | Identifiant unique de la machine | 1-50 (simulé), 51-100 (AI4I) | Toutes sources |
| `usine_id` | string | Code de l'usine | USN-FR-01 à USN-ES-02 | Enrichissement MSPR 2 |
| `usine_nom` | string | Nom de la ville de l'usine | Lyon, Toulouse, Nantes, Barcelone, Madrid | Enrichissement MSPR 2 |
| `usine_pays` | string | Pays de l'usine | France, Espagne | Enrichissement MSPR 2 |
| `ligne_production` | string | Ligne de production | LP-A, LP-B, LP-C | Enrichissement MSPR 2 |
| `type_piece` | string | Type de pièce fabriquée | Arbre_moteur, Disque_frein, etc. | Enrichissement MSPR 2 |
| `machine_profile` | string | Profil de fiabilité | robuste, standard, fragile, vieillissante | Toutes sources |
| `data_source` | string | **Source des données** | MECHA_simulated, AI4I_2020_real | Traçabilité |

### Colonnes de capteurs (données IoT)

| Colonne | Type | Unité | Description | Plage typique | Corrélation maintenance |
|---------|------|-------|-------------|---------------|------------------------|
| `temperature` | float | °C | Température capteur machine | 25 – 125°C | **forte** |
| `vibration` | float | mm/s | Niveau de vibration | 0 – 120 | modérée |
| `humidity` | float | % | Humidité ambiante | 30% – 80% | ~0 (nulle) |
| `pressure` | float | bar | Pression de fonctionnement | 0.5 – 5.0 | ~0 (nulle) |
| `energy_consumption` | float | kWh | Consommation énergétique | 0.3 – 7.0 | faible |

### Colonnes spécifiques AI4I 2020 (nouvelles)

| Colonne | Type | Unité | Description | Plage | Disponibilité |
|---------|------|-------|-------------|-------|---------------|
| `torque_nm` | float | Nm | Couple de la machine-outil | 3 – 80 | AI4I uniquement |
| `rotational_speed_rpm` | int | rpm | Vitesse de rotation | 1000 – 3000 | AI4I uniquement |
| `tool_wear_min` | int | min | Temps d'usure de l'outil | 0 – 240 | AI4I uniquement |
| `product_quality` | string | — | Qualité du produit (Low/Med/High) | L, M, H | AI4I uniquement |

> **Note** : Ces colonnes sont `NaN` pour les enregistrements MECHA simulés.
> Elles enrichissent le dataset avec des informations d'usure outil et de couple,
> pertinentes pour la maintenance prédictive en usinage.

### Colonnes d'état machine

| Colonne | Type | Description | Valeurs | Notes |
|---------|------|-------------|---------|-------|
| `machine_status` | int | État opérationnel | 0=Arrêt, 1=Fonct, 2=Panne | **NE PAS UTILISER comme feature ML** |
| `anomaly_flag` | int (0/1) | Signal d'anomalie | 0=Normal, 1=Anomalie | Seuils temp/vibr/dégradation |
| `predicted_remaining_life` | int | Durée de vie résiduelle (RUL) | 0 – 500 min | **Corrélation très forte** |
| `failure_type` | string | Type de panne | Normal, Overheating, Vibration_Issue, etc. | Catégoriel |
| `maintenance_required` | int (0/1) | **Variable cible ML** | 0=Non, 1=Oui | Déséquilibre ~90/10 (après fusion) |
| `maintenance_type` | string | Type de maintenance | none, preventive, corrective, recommended | Enrichissement MSPR 2 |

### Features temporelles

| Colonne | Type | Fenêtre | Description |
|---------|------|---------|-------------|
| `temp_rolling_10min` | float | 10 min | Moyenne mobile température |
| `temp_trend_1h` | float | 60 min | Tendance température (pente linéaire) |
| `vibr_rolling_10min` | float | 10 min | Moyenne mobile vibration |
| `temp_std_30min` | float | 30 min | Écart-type température (stabilité) |
| `energy_vibr_ratio` | float | — | Ratio énergie/vibration (efficacité) |

### Score de risque

| Colonne | Type | Description | Formule | Plage |
|---------|------|-------------|---------|-------|
| `downtime_risk` | float | Score composite de risque d'arrêt | 0.3×temp_risk + 0.25×vibr_risk + 0.45×rul_risk | 0.0 – 1.0 |

## Mapping des types de pannes

| AI4I 2020 (original) | MECHA (harmonisé) | Description |
|---------------------|-------------------|-------------|
| TWF (Tool Wear Failure) | Tool_Wear_Failure | Rupture outil par usure (200-240 min) |
| HDF (Heat Dissipation Failure) | Overheating | Défaut de dissipation thermique |
| PWF (Power Failure) | Electrical_Fault | Puissance hors limites |
| OSF (Overstrain Failure) | Vibration_Issue | Surcharge mécanique |
| RNF (Random Failure) | Random_Failure | Panne aléatoire (0.1%) |

## Hypothèses et limites

### Données MECHA simulées
1. Cycle de production 6h-22h, dégradation progressive
2. 4 profils de machines (robuste → vieillissante)
3. Humidity/pressure non informatives (par construction)

### Données AI4I 2020
1. Températures converties de Kelvin → Celsius
2. Vitesse de rotation normalisée en vibration (corrélation physique)
3. Machine IDs 51-100 pour les distinguer des machines simulées
4. Colonnes torque/tool_wear/rotational_speed conservées comme enrichissement

### Limites globales
- Le dataset hybride mélange données simulées et conformes aux specs AI4I
- Les features temporelles sont recalculées après fusion
- Les colonnes AI4I sont `NaN` pour les enregistrements MECHA (et inversement pour certaines)
- Le split temporel ML doit être recalculé sur le dataset fusionné


> **Version** : 2.0 | **Date** : Mai 2026 | **Auteur** : Équipe MECHA  
> **Source** : Dataset simulé enrichi, basé sur le Smart Manufacturing IoT-Cloud Monitoring Dataset (MSPR 1)

## Vue d'ensemble

| Propriété | Valeur |
|-----------|--------|
| Nombre d'enregistrements | ~100 000 |
| Nombre de colonnes | 25 |
| Machines couvertes | 50 (IDs 1 à 50) |
| Usines | 5 (3 France, 2 Espagne) |
| Plage temporelle | 01/01/2025 → 03/01/2025 (3 jours) |
| Granularité | ~1 enregistrement par minute par machine |
| Taille fichier | ~16 Mo (CSV) |

## Description des colonnes

### Colonnes d'identification

| Colonne | Type | Description | Valeurs / Plage | Origine |
|---------|------|-------------|-----------------|---------|
| `timestamp` | datetime | Horodatage de la mesure | 01/01/2025 – 03/01/2025 | Simulé |
| `machine_id` | int | Identifiant unique de la machine | 1 à 50 | Simulé |
| `usine_id` | string | Code de l'usine | USN-FR-01, USN-FR-02, USN-FR-03, USN-ES-01, USN-ES-02 | Enrichissement MSPR 2 |
| `usine_nom` | string | Nom de la ville de l'usine | Lyon, Toulouse, Nantes, Barcelone, Madrid | Enrichissement MSPR 2 |
| `usine_pays` | string | Pays de l'usine | France, Espagne | Enrichissement MSPR 2 |
| `ligne_production` | string | Ligne de production assignée | LP-A, LP-B, LP-C | Enrichissement MSPR 2 |
| `type_piece` | string | Type de pièce fabriquée | Arbre_moteur, Disque_frein, Carter_boite, Pale_turbine, Axe_roue | Enrichissement MSPR 2 |
| `machine_profile` | string | Profil de fiabilité de la machine | robuste, standard, fragile, vieillissante | Enrichissement MSPR 2 |

### Colonnes de capteurs (données IoT)

| Colonne | Type | Unité | Description | Plage typique | Corrélation maintenance |
|---------|------|-------|-------------|---------------|------------------------|
| `temperature` | float | °C | Température capteur machine | 28 – 125°C | **+0.28 (forte)** |
| `vibration` | float | mm/s | Niveau de vibration | 0 – 110 | +0.11 (modérée) |
| `humidity` | float | % | Humidité ambiante | 30% – 80% | ~0 (nulle) |
| `pressure` | float | bar | Pression de fonctionnement | 0.5 – 5.0 | ~0 (nulle) |
| `energy_consumption` | float | kWh | Consommation énergétique | 0.3 – 7.0 | +0.05 (faible) |

### Colonnes d'état machine

| Colonne | Type | Description | Valeurs | Notes |
|---------|------|-------------|---------|-------|
| `machine_status` | int | État opérationnel | 0=Arrêt planifié, 1=Fonctionnement, 2=Panne | ⚠️ **NE PAS UTILISER comme feature ML** (data leakage) |
| `anomaly_flag` | int (0/1) | Signal d'anomalie détectée | 0=Normal, 1=Anomalie | Basé sur seuils temp/vibr/dégradation |
| `predicted_remaining_life` | int | Durée de vie résiduelle estimée (RUL) | 0 – 500 min | **Corrélation -0.34 (très forte)** |
| `failure_type` | string | Type de panne identifié | Normal, Overheating, Vibration_Issue, Pressure_Drop, Electrical_Fault | Catégoriel |
| `maintenance_required` | int (0/1) | **Variable cible ML** | 0=Non, 1=Oui | ~97% négatif / ~3% positif |
| `maintenance_type` | string | Type de maintenance | none, preventive, corrective, recommended | Enrichissement MSPR 2 |

### Features temporelles (enrichissement MSPR 2)

| Colonne | Type | Fenêtre | Description | Formule |
|---------|------|---------|-------------|---------|
| `temp_rolling_10min` | float | 10 min | Moyenne mobile température | mean(temperature[-10:]) |
| `temp_trend_1h` | float | 60 min | Tendance température (pente) | polyfit(temperature[-60:], deg=1)[0] |
| `vibr_rolling_10min` | float | 10 min | Moyenne mobile vibration | mean(vibration[-10:]) |
| `temp_std_30min` | float | 30 min | Écart-type température | std(temperature[-30:]) |
| `energy_vibr_ratio` | float | — | Ratio énergie/vibration | energy_consumption / vibration |

### Score de risque

| Colonne | Type | Description | Formule | Plage |
|---------|------|-------------|---------|-------|
| `downtime_risk` | float | Score composite de risque d'arrêt | 0.3×temp_risk + 0.25×vibr_risk + 0.45×rul_risk | 0.0 – 1.0 |

## Usines MECHA

| Code usine | Ville | Pays | Machines | Particularité |
|-----------|-------|------|----------|---------------|
| USN-FR-01 | Lyon | France | 1 à 10 | Site historique, équipement IoT avancé |
| USN-FR-02 | Toulouse | France | 11 à 20 | Spécialisé aéronautique |
| USN-FR-03 | Nantes | France | 21 à 30 | Plus récent, standard |
| USN-ES-01 | Barcelone | Espagne | 31 à 40 | Ouvert récemment, coûts optimisés |
| USN-ES-02 | Madrid | Espagne | 41 à 50 | Site de test, machines variées |

## Profils de machines

| Profil | Machines | Temp. base | Vibr. base | Prob. panne | Description |
|--------|----------|-----------|-----------|-------------|-------------|
| robuste | 1, 10, 20, 30, 40, 50 | 70°C | 35 mm/s | 2% | Machines récentes, bien entretenues |
| standard | 32 machines | 75°C | 40 mm/s | 4% | Profil moyen de la flotte |
| fragile | 3, 8, 15, 22, 32, 41, 48 | 82°C | 50 mm/s | 8% | Machines nécessitant plus de suivi |
| vieillissante | 5, 12, 24, 37, 43 | 85°C | 55 mm/s | 10% | Machines en fin de vie, remplacement prévu |

## Hypothèses de simulation

1. **Cycle de production** : 6h-22h (arrêt planifié la nuit)
2. **Dégradation progressive** : chaque minute en fonctionnement augmente la dégradation
3. **Taux de dégradation** : proportionnel au profil de fragilité de la machine
4. **Pannes** : se déclenchent quand la dégradation dépasse 85% avec une probabilité liée au profil
5. **Maintenance corrective** : durée de 30 min à 2h, reset de la dégradation à 0
6. **Maintenance préventive** : possible après >3h de fonctionnement si dégradation >40%
7. **Température** : base + dégradation × 40°C + bruit gaussien
8. **Vibration** : base + dégradation × 30 mm/s + bruit gaussien
9. **Humidité/Pression** : distribution uniforme, non corrélées à la dégradation (volontairement)

## Limites connues

- Dataset **simulé** — ne reflète pas la complexité réelle d'un environnement industriel
- Seulement **3 jours** de données (vs 69 jours en MSPR 1)
- Déséquilibre prononcé de la variable cible (~97/3)
- Humidité et pression non informatives (par construction)
- Pas de données opérateurs (conformité RGPD)
- Pas de données de qualité produit (taux de rebuts)
