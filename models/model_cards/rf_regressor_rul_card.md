# Model Card : Random Forest Regressor (RUL)

## Informations Generales

| Champ | Valeur |
|-------|--------|
| **Nom du modele** | Random Forest Regressor (RUL) |
| **Version** | 1.0.0 |
| **Date de creation** | 2026-05-30 |
| **Framework** | scikit-learn |
| **Type** | Regression (prediction de la duree de vie restante) |
| **Statut** | Modele complementaire |
| **Projet** | MECHA - MSPR 2, Bloc 4, EPSI RNCP35584 |

## Description

Modele de regression base sur un ensemble d'arbres de decision (Random Forest) pour la prediction de la duree de vie restante (RUL - Remaining Useful Life) des machines. Contrairement aux modeles de classification qui predisent SI une maintenance est necessaire, ce modele predit QUAND la maintenance sera necessaire en estimant le nombre d'unites de temps restantes avant defaillance.

### Objectif

Estimer la valeur de `predicted_remaining_life` a partir des mesures capteurs (temperature, vibration, etc.), permettant une planification fine des interventions de maintenance.

## Cas d'Usage Prevu

### Utilisation principale
- **Planification de maintenance** : Estimer le temps restant avant intervention necessaire
- **Priorisation** : Classer les machines par urgence de maintenance
- **Optimisation des stocks** : Anticiper les besoins en pieces de rechange
- **KPI operationnel** : Fournir un indicateur continu de sante machine

### Utilisateurs cibles
- Planificateurs de maintenance
- Responsables de production
- Tableaux de bord operationnels

### Hors perimetre
- Ne predit PAS le type de defaillance
- Ne remplace PAS les modeles de classification pour la decision binaire de maintenance
- La prediction est une estimation, pas une certitude

## Donnees d'Entrainement

### Source
- **Dataset** : `mecha_dataset_processed.csv`
- **Volume** : ~100,000 lignes
- **Variable cible** : `predicted_remaining_life`

### Split des donnees
- **Methode** : Split temporel 80/20
- **Coherence** : Meme split que les modeles de classification

### Features utilisees (11)

| Feature | Description | Type |
|---------|-------------|------|
| `temperature` | Temperature machine | Numerique |
| `vibration` | Niveau de vibration | Numerique |
| `humidity` | Taux d'humidite | Numerique |
| `pressure` | Pression | Numerique |
| `energy_consumption` | Consommation energetique | Numerique |
| `temp_rolling_10min` | Moyenne glissante temperature | Numerique |
| `temp_trend_1h` | Tendance temperature | Numerique |
| `vibr_rolling_10min` | Moyenne glissante vibration | Numerique |
| `temp_std_30min` | Ecart-type temperature | Numerique |
| `energy_vibr_ratio` | Ratio energie/vibration | Numerique |
| `downtime_risk` | Score de risque d'arret | Numerique |

**Note** : `predicted_remaining_life` est EXCLUE des features car c'est la variable cible.

### Features EXCLUES

| Feature exclue | Raison |
|----------------|--------|
| `machine_status` | **DATA LEAKAGE** |
| `predicted_remaining_life` | Variable cible (pour ce modele) |

## Hyperparametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| `n_estimators` | 200 | Bon compromis performance/temps |
| `max_depth` | 15 | Limiter le surapprentissage |
| `min_samples_split` | 10 | Regularisation |
| `min_samples_leaf` | 5 | Regularisation |
| `max_features` | sqrt | Standard pour la regression ensemble |
| `random_state` | 42 | Reproductibilite |

## Metriques de Performance

> Sauvegardees dans `models/evaluation/results/rf_regressor_rul_metrics.json`.

### Metriques de regression

| Metrique | Description |
|----------|-------------|
| **MAE** | Mean Absolute Error - erreur absolue moyenne |
| **RMSE** | Root Mean Squared Error - racine de l'erreur quadratique moyenne |
| **R2 Score** | Coefficient de determination (1 = parfait, 0 = modele naif) |
| **MSE** | Mean Squared Error |

### Interpretation
- **MAE** : En moyenne, l'erreur de prediction en unites de temps
- **R2** : Proportion de la variance de la RUL expliquee par le modele
- **RMSE** : Penalise davantage les grandes erreurs (utile pour les cas critiques)

## Limites et Risques

### Limites connues
1. **Precision de la RUL** : La variable cible (`predicted_remaining_life`) est elle-meme une estimation, pas une verite terrain mesuree
2. **Distribution de la RUL** : La plupart des valeurs de RUL sont elevees (machines en bon etat), le modele peut etre moins precis pour les faibles RUL
3. **Non-stationnarite** : Les patterns de degradation peuvent varier selon les types de machines et conditions
4. **Intervalle de confiance** : Le modele fournit une prediction ponctuelle sans intervalle de confiance

### Risques
- **Surestimation de la RUL** : Dangereux, peut retarder une maintenance necessaire
- **Sous-estimation de la RUL** : Moins critique, mais genere des interventions prematurees
- **Confiance excessive** : Les utilisateurs pourraient accorder trop de confiance a une estimation ponctuelle

## Biais Potentiels

| Type de biais | Description | Mitigation |
|---------------|-------------|------------|
| Biais de distribution | RUL souvent elevee, sous-representation des faibles RUL | Enrichissement des donnees de degradation |
| Biais de machine | Degradation differente selon le type de machine | Features de contexte (machine_profile) possibles |
| Biais de capteur | Precision variable des capteurs | Preprocessing et validation des donnees |
| Biais de label | La RUL cible est estimee, pas mesuree | Documentation de la methode de calcul de RUL |

## Maintenance du Modele

### Reexamen
- **Frequence** : Trimestrielle
- **Critere** : Comparaison MAE predite vs MAE sur les nouvelles donnees
- **Responsable** : Equipe Data MECHA

### Monitoring
- Suivi de l'erreur de prediction en production
- Comparaison avec les durees de vie reelles observees
- Detection de derive dans la distribution des predictions

## Conformite EU AI Act

| Exigence | Statut |
|----------|--------|
| Transparence | Model card documentee |
| Donnees documentees | Oui |
| Metriques de performance | Oui (metriques de regression) |
| Limites et biais | Oui |
| Responsabilite humaine | Outil de planification, validation humaine requise |
| Classification de risque | Risque limite |

## References

- scikit-learn : https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- Saxena, A. et al. (2008). Damage propagation modeling for aircraft engine run-to-failure simulation
- EU AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689
