# Model Card : Isolation Forest

## Informations Generales

| Champ | Valeur |
|-------|--------|
| **Nom du modele** | Isolation Forest |
| **Version** | 1.0.0 |
| **Date de creation** | 2026-05-30 |
| **Framework** | scikit-learn |
| **Type** | Detection d'anomalies (non supervise) |
| **Statut** | Modele complementaire |
| **Projet** | MECHA - MSPR 2, Bloc 4, EPSI RNCP35584 |

## Description

Modele de detection d'anomalies non supervise base sur l'Isolation Forest. Contrairement aux modeles de classification supervises (RF, XGBoost, LR), ce modele n'utilise PAS la variable cible `maintenance_required` pendant l'entrainement. Il identifie les points de donnees anormaux en mesurant leur facilite d'isolation dans un ensemble d'arbres aleatoires.

### Principe de fonctionnement
Les anomalies sont des points de donnees qui sont faciles a isoler : ils necessitent moins de coupures aleatoires pour etre separes du reste des donnees. L'algorithme construit des arbres aleatoires et mesure la profondeur moyenne necessaire pour isoler chaque point.

### Objectif

Detecter les comportements anormaux des machines (anomalies capteurs) qui pourraient indiquer un besoin de maintenance, sans necessite d'etiquettes historiques.

## Cas d'Usage Prevu

### Utilisation principale
- **Detection d'anomalies** : Identifier les comportements machines inhabituels
- **Surveillance continue** : Monitoring en temps reel des capteurs IoT
- **Alerte precoce** : Detection de degradation avant que les seuils classiques ne soient atteints
- **Complement** : Utilise en complement des modeles supervises

### Utilisateurs cibles
- Systemes de monitoring en temps reel
- Equipes de maintenance pour les alertes de comportement anormal
- Equipe Data Science pour l'exploration de patterns inhabituels

### Hors perimetre
- Ne fournit PAS de diagnostic (type de panne)
- Ne predit PAS la duree de vie restante
- Ne remplace PAS les modeles supervises pour la decision de maintenance

## Donnees d'Entrainement

### Source
- **Dataset** : `mecha_dataset_processed.csv`
- **Volume** : ~80,000 lignes (80% du dataset, split temporel)
- **Particularite** : Entrainement NON supervise (pas de variable cible)

### Features utilisees (12)
Identiques aux autres modeles :
`temperature`, `vibration`, `humidity`, `pressure`, `energy_consumption`, `predicted_remaining_life`, `temp_rolling_10min`, `temp_trend_1h`, `vibr_rolling_10min`, `temp_std_30min`, `energy_vibr_ratio`, `downtime_risk`

### Features EXCLUES

| Feature exclue | Raison |
|----------------|--------|
| `machine_status` | **DATA LEAKAGE** |

## Hyperparametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| `n_estimators` | 200 | Nombre d'arbres pour la detection |
| `contamination` | 0.05 | Proportion attendue d'anomalies (5%) |
| `max_features` | 1.0 | Utiliser toutes les features |
| `random_state` | 42 | Reproductibilite |

### Note sur la contamination
La valeur de `contamination=0.05` est une estimation. Le taux reel de maintenance requise est de ~3.1%, mais les anomalies capteurs peuvent etre plus frequentes que les maintenances effectives. Ce parametre peut etre ajuste selon les retours terrain.

## Metriques de Performance

> Sauvegardees dans `models/evaluation/results/isolation_forest_metrics.json`.

### Metriques principales

| Metrique | Description |
|----------|-------------|
| **Accuracy** | Correspondance anomalies detectees vs maintenance reelle |
| **Precision** | Parmi les anomalies detectees, combien correspondent a une maintenance |
| **Recall** | Parmi les maintenances reelles, combien ont ete detectees comme anomalies |
| **F1-Score** | Moyenne harmonique |
| **AUC-ROC** | Basee sur le decision_function |
| **Contamination effective** | Taux reel d'anomalies detectees |

### Interpretation des metriques
Etant un modele non supervise, les metriques de classification sont calculees a posteriori en comparant les anomalies detectees avec `maintenance_required`. Un faible F1-Score n'indique pas necessairement un mauvais modele : les anomalies capteurs ne correspondent pas toujours a un besoin de maintenance.

## Limites et Risques

### Limites connues
1. **Non supervise** : Ne distingue pas les types d'anomalies (maintenance, erreur capteur, changement de production)
2. **Contamination fixe** : Le parametre `contamination` est une estimation qui peut ne pas refleter la realite
3. **Sensibilite aux outliers** : Des valeurs extremes non pertinentes peuvent etre classees comme anomalies
4. **Pas de probabilite** : Fournit un score d'anomalie, pas une probabilite calibree
5. **Correlation imparfaite** : Les anomalies detectees ne correspondent pas necessairement aux besoins de maintenance

### Risques
- **Faux positifs excessifs** : Trop d'alertes d'anomalies creent de la fatigue d'alerte
- **Anomalies non pertinentes** : Certaines anomalies detectees sont des variations normales de production
- **Manque de contexte** : L'anomalie est detectee sans explication de la cause

## Biais Potentiels

| Type de biais | Description | Mitigation |
|---------------|-------------|------------|
| Biais de normalite | Le modele apprend ce qui est "normal" a partir des donnees d'entrainement | Entrainement periodique avec des donnees recentes |
| Biais de contamination | Le parametre fixe peut sur/sous-estimer les anomalies | Ajustement base sur les retours terrain |
| Biais de feature | Certaines features peuvent dominer la detection d'anomalies | Analyse des scores d'anomalie par feature |

## Maintenance du Modele

### Reexamen
- **Frequence** : Mensuelle (les patterns normaux evoluent)
- **Critere** : Taux de faux positifs en production
- **Responsable** : Equipe Data MECHA

### Monitoring
- Suivi du taux d'anomalies detectees
- Correlation avec les maintenances effectuees
- Ajustement du seuil de contamination si necessaire
- Detection de derive dans la distribution des scores d'anomalie

## Conformite EU AI Act

| Exigence | Statut |
|----------|--------|
| Transparence | Model card documentee |
| Donnees documentees | Oui |
| Metriques de performance | Oui (avec reserve sur l'interpretation) |
| Limites et biais | Oui |
| Responsabilite humaine | Outil d'alerte, validation humaine requise |
| Classification de risque | Risque limite (alerte, pas de decision autonome) |

## References

- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation Forest
- scikit-learn : https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- EU AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689
