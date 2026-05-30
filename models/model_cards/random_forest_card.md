# Model Card : Random Forest Classifier

## Informations Generales

| Champ | Valeur |
|-------|--------|
| **Nom du modele** | Random Forest Classifier |
| **Version** | 1.0.0 |
| **Date de creation** | 2026-05-30 |
| **Framework** | scikit-learn |
| **Type** | Classification binaire |
| **Statut** | Modele principal (prioritaire) |
| **Projet** | MECHA - MSPR 2, Bloc 4, EPSI RNCP35584 |

## Description

Modele de classification binaire base sur un ensemble d'arbres de decision (Random Forest) pour la prediction de la necessite de maintenance sur les machines de production MECHA. Ce modele est le **modele principal** selectionne lors de la MSPR 1 (F1=71%) et optimise dans cette iteration.

### Objectif

Predire si une machine necessite une intervention de maintenance (`maintenance_required = 1`) a partir des donnees capteurs IoT en temps reel, afin de planifier les interventions avant les pannes.

## Cas d'Usage Prevu

### Utilisation principale
- **Maintenance predictive** : Detection proactive des besoins de maintenance sur 5 usines MECHA (aeronautique/automobile)
- **Planification** : Aide a la decision pour les equipes de maintenance
- **Reduction des arrets** : Minimiser les arrets non planifies en anticipant les defaillances

### Utilisateurs cibles
- Responsables de maintenance des usines MECHA
- Ingenieurs de production
- Systemes automatises de planification de maintenance

### Hors perimetre
- Ce modele ne remplace PAS le jugement humain
- Ne doit PAS etre utilise comme seul critere de decision pour des pieces critiques aeronautiques
- N'est PAS prevu pour des machines hors du parc MECHA

## Donnees d'Entrainement

### Source
- **Dataset** : `mecha_dataset_processed.csv`
- **Volume** : ~100,000 lignes de mesures capteurs IoT
- **Periode** : Donnees temporelles (2025)
- **Usines** : 5 sites de production (France, Allemagne, etc.)

### Split des donnees
- **Methode** : Split temporel 80/20 (PAS aleatoire)
- **Train** : 80% premiers echantillons chronologiquement
- **Test** : 20% derniers echantillons chronologiquement
- **Justification** : Eviter le data leakage temporel ; on entraine sur le passe, on teste sur le futur

### Features utilisees (12)

| Feature | Description | Type |
|---------|-------------|------|
| `temperature` | Temperature machine (degres C) | Numerique |
| `vibration` | Niveau de vibration | Numerique |
| `humidity` | Taux d'humidite (%) | Numerique |
| `pressure` | Pression (bar) | Numerique |
| `energy_consumption` | Consommation energetique | Numerique |
| `predicted_remaining_life` | Duree de vie restante estimee | Numerique |
| `temp_rolling_10min` | Moyenne glissante temperature 10min | Numerique |
| `temp_trend_1h` | Tendance temperature 1h | Numerique |
| `vibr_rolling_10min` | Moyenne glissante vibration 10min | Numerique |
| `temp_std_30min` | Ecart-type temperature 30min | Numerique |
| `energy_vibr_ratio` | Ratio energie/vibration | Numerique |
| `downtime_risk` | Score de risque d'arret | Numerique |

### Features EXCLUES (data leakage)

| Feature exclue | Raison |
|----------------|--------|
| `machine_status` | **DATA LEAKAGE** confirme en MSPR 1 : cette variable encode directement l'etat de la machine et fuit l'information cible |

### Desequilibre des classes

| Classe | Proportion |
|--------|------------|
| 0 (pas de maintenance) | ~96.9% |
| 1 (maintenance requise) | ~3.1% |

**Gestion** : `class_weight='balanced'` -- ajuste automatiquement les poids inversement proportionnels a la frequence des classes.

## Hyperparametres

| Parametre | Valeur | Justification |
|-----------|--------|---------------|
| `n_estimators` | 200 | Bon compromis performance/temps |
| `max_depth` | 15 | Limiter le surapprentissage |
| `min_samples_split` | 10 | Regularisation |
| `min_samples_leaf` | 5 | Regularisation |
| `class_weight` | balanced | Gestion du desequilibre 96.9/3.1 |
| `max_features` | sqrt | Standard pour la classification |
| `random_state` | 42 | Reproductibilite |
| `n_jobs` | -1 | Parallelisation maximale |

## Metriques de Performance

> Les metriques exactes sont generees automatiquement lors de l'entrainement
> et sauvegardees dans `models/evaluation/results/random_forest_metrics.json`.

| Metrique | Description |
|----------|-------------|
| **Accuracy** | Taux de predictions correctes |
| **Precision** | Parmi les alertes declenchees, combien sont justifiees |
| **Recall** | Parmi les maintenances reelles, combien sont detectees |
| **F1-Score** | Moyenne harmonique precision/recall (metrique principale) |
| **AUC-ROC** | Capacite de discrimination du modele |

### Metrique principale : F1-Score

Le F1-Score est la metrique principale car :
- L'accuracy seule est trompeuse avec 96.9% de classe majoritaire (un modele naif atteint 96.9% en predisant toujours 0)
- Le recall est critique (ne pas manquer une maintenance = securite)
- La precision est importante (eviter les faux positifs = couts d'arret inutiles)

## Limites et Risques

### Limites connues
1. **Desequilibre extreme** : Avec 3.1% de positifs, le modele peut avoir du mal a detecter tous les cas de maintenance
2. **Donnees synthetiques** : Le dataset est issu de simulations, les performances en production reelle peuvent differer
3. **Derive temporelle** : Les performances peuvent se degrader si les conditions d'exploitation changent (concept drift)
4. **Generalisation** : Entraine sur des machines MECHA specifiques, peut ne pas generaliser a d'autres types de machines

### Risques
- **Faux negatifs** : Ne pas detecter une maintenance necessaire peut entrainer une panne
- **Faux positifs** : Declencher une maintenance inutile engendre des couts
- **Surapprentissage** : Malgre la regularisation, risque de surapprentissage sur les patterns specifiques du dataset

## Biais Potentiels

| Type de biais | Description | Mitigation |
|---------------|-------------|------------|
| Biais temporel | Le modele peut apprendre des patterns saisonniers specifiques | Split temporel + monitoring continu |
| Biais de machine | Certaines machines peuvent etre surrepresentees | Verification de la distribution par machine_id |
| Biais de capteur | Des capteurs defaillants peuvent introduire du bruit | Preprocessing et detection d'outliers |
| Biais de selection | Le dataset peut ne pas couvrir tous les types de pannes | Enrichissement continu des donnees |

## Maintenance du Modele

### Reexamen
- **Frequence** : Trimestrielle, ou apres tout changement significatif dans les donnees
- **Critere de reentrainement** : Baisse du F1-Score de plus de 5% par rapport a la baseline
- **Responsable** : Equipe Data MECHA

### Monitoring en production
- Suivi du F1-Score sur les predictions en production
- Detection de concept drift (distribution des features)
- Alertes si le taux de faux negatifs depasse un seuil critique
- Comparaison periodique avec les maintenances reellement effectuees

## Conformite EU AI Act

| Exigence | Statut |
|----------|--------|
| Transparence du modele | Model card documentee |
| Donnees d'entrainement documentees | Oui |
| Metriques de performance | Oui |
| Limites et biais documentes | Oui |
| Responsabilite humaine | Le modele est un outil d'aide a la decision |
| Classification de risque | Risque limite (industrie, pas de decision directe sur les personnes) |

## References

- MSPR 1 : Validation du Random Forest comme modele prioritaire (F1=71%)
- scikit-learn : https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- EU AI Act : https://eur-lex.europa.eu/eli/reg/2024/1689
