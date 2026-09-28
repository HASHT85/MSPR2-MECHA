# Model Card : XGBoost Classifier

## Informations Generales

| Champ | Valeur |
|-------|--------|
| **Nom du modele** | XGBoost Classifier |
| **Version** | 1.0.0 |
| **Date de creation** | 2026-05-30 |
| **Framework** | XGBoost (xgboost) |
| **Type** | Classification binaire (gradient boosting) |
| **Statut** | Modele alternatif |
| **Projet** | MECHA - MSPR 2, Bloc 4, EPSI RNCP35584 |

## Description

Modele de classification binaire base sur le gradient boosting (XGBoost) pour la prediction de maintenance. XGBoost est une alternative au Random Forest offrant potentiellement de meilleures performances grace a l'apprentissage sequentiel et la regularisation integree.

### Objectif

Predire si une machine necessite une intervention de maintenance (`maintenance_required = 1`) a partir des donnees capteurs IoT. Ce modele sert d'alternative au Random Forest pour comparer les approches.

## Cas d'Usage Prevu

### Utilisation principale
- **Maintenance predictive** : Alternative au Random Forest pour la detection de besoins de maintenance
- **Benchmark** : Comparaison des performances avec l'approche ensemble (Random Forest)
- **Production** : Peut remplacer le RF si les performances sont superieures

### Utilisateurs cibles
- Equipe Data Science MECHA
- Responsables de maintenance (en cas de deploiement)

### Hors perimetre
- Meme cadre que le Random Forest : outil d'aide a la decision, pas de decision autonome

## Donnees d'Entrainement

### Source
- **Dataset** : `mecha_dataset_processed.csv`
- **Volume** : ~100,000 lignes de mesures capteurs IoT
- **Periode** : Donnees temporelles (2025)

### Split des donnees
- **Methode** : Split temporel 80/20 (identique au Random Forest)
- **Justification** : Coherence dans la comparaison des modeles

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

| Classe | Proportion |
|--------|------------|
| 0 (pas de maintenance) | ~96.9% |
| 1 (maintenance requise) | ~3.1% |

**Gestion** : `scale_pos_weight = n_negatifs / n_positifs` -- compense le desequilibre en augmentant le poids des positifs dans la fonction de cout.

## Hyperparametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| `n_estimators` | 200 | Nombre d'arbres boosted |
| `max_depth` | 8 | Plus faible que RF car le boosting accumule la complexite |
| `learning_rate` | 0.1 | Taux d'apprentissage standard |
| `scale_pos_weight` | ~31.3 | Ratio negatifs/positifs pour compenser le desequilibre |
| `subsample` | 0.8 | Regularisation par sous-echantillonnage |
| `colsample_bytree` | 0.8 | Regularisation par selection de features |
| `reg_alpha` | 0.1 | Regularisation L1 |
| `reg_lambda` | 1.0 | Regularisation L2 |
| `eval_metric` | logloss | Metrique d'optimisation |
| `random_state` | 42 | Reproductibilite |

## Metriques de Performance

> Les metriques exactes sont generees automatiquement lors de l'entrainement
> et sauvegardees dans `models/evaluation/results/xgboost_metrics.json`.

| Metrique | Description |
|----------|-------------|
| **Accuracy** | Taux de predictions correctes |
| **Precision** | Ratio vrais positifs / (vrais positifs + faux positifs) |
| **Recall** | Ratio vrais positifs / (vrais positifs + faux negatifs) |
| **F1-Score** | Moyenne harmonique precision/recall |
| **AUC-ROC** | Aire sous la courbe ROC |

### Avantages de XGBoost vs Random Forest
- Meilleure gestion des interactions complexes entre features
- Regularisation integree (L1, L2)
- Gestion native du desequilibre via `scale_pos_weight`
- Potentiellement plus performant sur les features a forte importance

## Limites et Risques

### Limites connues
1. **Complexite** : Plus difficile a interpreter que le Random Forest
2. **Sensibilite aux hyperparametres** : Necessite un tuning plus fin
3. **Temps d'entrainement** : Potentiellement plus long que le RF
4. **Surapprentissage** : Le boosting est plus sujet au surapprentissage si mal regularise
5. **Dependance externe** : Necessite la librairie xgboost (non incluse dans scikit-learn)

### Risques
- Memes risques que le Random Forest (faux negatifs, faux positifs)
- Risque additionnel : complexite du modele rendant le debugging plus difficile

## Biais Potentiels

| Type de biais | Description | Mitigation |
|---------------|-------------|------------|
| Biais temporel | Patterns saisonniers specifiques | Split temporel |
| Biais d'optimisation | Le boosting peut sur-optimiser certains patterns | Regularisation L1/L2, early stopping |
| Biais de machine | Surrepresentation de certaines machines | Monitoring par machine_id |

## Maintenance du Modele

### Reexamen
- **Frequence** : Trimestrielle
- **Critere** : Comparaison continue avec le Random Forest
- **Responsable** : Equipe Data MECHA

### Monitoring
- Suivi des metriques en production
- Comparaison periodique RF vs XGBoost
- Detection de derive (concept drift)

## Conformite EU AI Act

| Exigence | Statut |
|----------|--------|
| Transparence | Model card documentee |
| Donnees documentees | Oui |
| Metriques de performance | Oui |
| Limites et biais | Oui |
| Responsabilite humaine | Outil d'aide a la decision |
| Classification de risque | Risque limite |

## References

- XGBoost : https://xgboost.readthedocs.io/
- Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System
- EU AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689
