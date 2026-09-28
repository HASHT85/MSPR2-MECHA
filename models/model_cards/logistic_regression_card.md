# Model Card : Regression Logistique

## Informations Generales

| Champ | Valeur |
|-------|--------|
| **Nom du modele** | Regression Logistique |
| **Version** | 1.0.0 |
| **Date de creation** | 2026-05-30 |
| **Framework** | scikit-learn |
| **Type** | Classification binaire (modele lineaire) |
| **Statut** | Baseline de reference |
| **Projet** | MECHA - MSPR 2, Bloc 4, EPSI RNCP35584 |

## Description

Modele de classification binaire lineaire servant de **baseline de reference** pour le projet MECHA. La regression logistique est un modele simple et interpretable qui permet d'etablir un seuil minimal de performance que les modeles plus complexes (Random Forest, XGBoost) doivent depasser.

### Objectif

Fournir une baseline de performance pour la classification de maintenance. Si les modeles complexes ne depassent pas significativement la regression logistique, cela indique un probleme dans les features ou les donnees.

## Cas d'Usage Prevu

### Utilisation principale
- **Baseline** : Reference de performance minimale
- **Interpretabilite** : Comprendre les relations lineaires entre features et cible
- **Validation** : Verifier que les modeles complexes apportent une reelle valeur ajoutee

### Utilisateurs cibles
- Equipe Data Science MECHA
- Parties prenantes necessitant une explication simple du modele

### Hors perimetre
- Non prevu pour le deploiement en production (sauf si performances superieures)

## Donnees d'Entrainement

### Source
- **Dataset** : `mecha_dataset_processed.csv`
- **Volume** : ~100,000 lignes
- **Split** : Temporel 80/20 (identique aux autres modeles)

### Preprocessing specifique
- **StandardScaler** : Normalisation des features (moyenne=0, ecart-type=1)
- **Justification** : La regression logistique est sensible a l'echelle des features (contrairement aux arbres de decision)

### Features utilisees (10, capteurs uniquement)

| Feature | Description | Type |
|---------|-------------|------|
| `temperature` | Temperature machine (degres C) | Numerique |
| `vibration` | Niveau de vibration (mm/s) | Numerique |
| `humidity` | Taux d'humidite (%) | Numerique |
| `pressure` | Pression (bar) | Numerique |
| `energy_consumption` | Consommation energetique (kWh) | Numerique |
| `temp_rolling_10min` | Moyenne glissante temperature 10min | Numerique |
| `temp_trend_1h` | Tendance temperature 1h | Numerique |
| `vibr_rolling_10min` | Moyenne glissante vibration 10min | Numerique |
| `temp_std_30min` | Ecart-type temperature 30min | Numerique |
| `energy_vibr_ratio` | Ratio energie/vibration | Numerique |

### Features EXCLUES (data leakage)

| Feature exclue | Raison |
|----------------|--------|
| `machine_status` | **DATA LEAKAGE** confirme en MSPR 1 : cette variable encode directement l'etat de la machine et fuit l'information cible |
| `predicted_remaining_life` | **DATA LEAKAGE** identifie en revue MSPR 2 : dans la simulation, RUL = 500 x (1 - degradation) et la cible vaut 1 des que degradation > 0.6 ; la regle « RUL < 200 » reproduit la cible a 99 % |
| `downtime_risk` | **DATA LEAKAGE** : score composite construit a 45 % a partir du RUL |

### Desequilibre des classes
**Gestion** : `class_weight='balanced'`

## Hyperparametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| `C` | 1.0 | Force de regularisation par defaut |
| `class_weight` | balanced | Gestion du desequilibre |
| `solver` | lbfgs | Optimiseur quasi-Newton, efficace pour les petits/moyens datasets |
| `max_iter` | 1000 | Assurer la convergence |
| `random_state` | 42 | Reproductibilite |

## Metriques de Performance

> Sauvegardees dans `models/evaluation/results/logistic_regression_metrics.json`.

| Metrique | Description |
|----------|-------------|
| **Accuracy** | Taux de predictions correctes |
| **Precision** | Vrais positifs / predictions positives |
| **Recall** | Vrais positifs / reels positifs |
| **F1-Score** | Moyenne harmonique |
| **AUC-ROC** | Discrimination du modele |

### Interpretation des coefficients
La regression logistique permet d'interpreter directement l'influence de chaque feature :
- Coefficient positif : augmente la probabilite de maintenance
- Coefficient negatif : diminue la probabilite de maintenance
- Magnitude : force de l'influence

## Limites et Risques

### Limites connues
1. **Linearite** : Suppose des relations lineaires entre features et log-odds de la cible
2. **Interactions** : Ne capture pas les interactions complexes entre features sans feature engineering
3. **Non-linearites** : Performances limitees si les patterns sont non-lineaires
4. **Performance attendue** : Inferieure aux modeles ensemble (RF, XGBoost) sur des donnees complexes

### Risques
- **Sous-performance** : Peut ne pas detecter suffisamment de cas de maintenance
- **Simplicite excessive** : Les relations capteurs-maintenance sont probablement non-lineaires

## Biais Potentiels

| Type de biais | Description | Mitigation |
|---------------|-------------|------------|
| Biais de linearite | Le modele ne capture que les relations lineaires | Utiliser comme baseline, pas comme modele principal |
| Biais d'echelle | Sensible a la normalisation | StandardScaler applique |
| Biais de features | Features multicollineaires peuvent affecter les coefficients | Verification VIF possible |

## Maintenance du Modele

### Reexamen
- **Frequence** : A chaque reentrainement des modeles principaux
- **Role** : Verifier que les modeles complexes restent superieurs a la baseline
- **Responsable** : Equipe Data MECHA

## Conformite EU AI Act

| Exigence | Statut |
|----------|--------|
| Transparence | Modele le plus interpretable |
| Donnees documentees | Oui |
| Metriques de performance | Oui |
| Limites et biais | Oui |
| Classification de risque | Risque limite (baseline, pas de deploiement autonome) |

## References

- scikit-learn : https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- EU AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689
