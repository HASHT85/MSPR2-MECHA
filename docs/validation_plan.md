# ✅ Plan de Validation et Tests — MECHA Predict

> **Projet** : MECHA — Maintenance Prédictive par Intelligence Artificielle  
> **Version** : 1.0  
> **Date** : 30/05/2026  
> **Auteurs** : Malek El Fayedh, Thibaut Doreau, Vincent Gonçalves, Pierre-Louis Guinel  
> **Compétence couverte** : **C5 — Réaliser les tests d'une application**

---

## 1. Introduction

Ce document définit la stratégie de test complète de la solution MECHA Predict. Il couvre l'ensemble des niveaux de test (unitaires, intégration, recette) et fournit les scénarios, jeux de données et critères d'acceptation nécessaires pour garantir la qualité et la fiabilité de la solution.

### 1.1 Objectifs

| Objectif | Description |
|----------|-------------|
| **Fiabilité** | Garantir que les prédictions sont correctes et exploitables |
| **Robustesse** | Vérifier le comportement en conditions dégradées |
| **Non-régression** | S'assurer que les évolutions ne cassent pas l'existant |
| **Conformité métier** | Valider que la solution répond aux besoins opérationnels |
| **Performance** | Vérifier les temps de réponse sous charge |

### 1.2 Périmètre

```mermaid
graph TD
    A["Plan de validation"] --> B["Tests unitaires<br/>(composant isolé)"]
    A --> C["Tests d'intégration<br/>(composants assemblés)"]
    A --> D["Tests de recette<br/>(scénarios métier)"]
    A --> E["Tests de performance<br/>(charge / stress)"]
    
    B --> B1["Pipeline données"]
    B --> B2["Modèles ML"]
    B --> B3["Endpoints API"]
    B --> B4["Fonctions utilitaires"]
    
    C --> C1["API ↔ Modèle ML"]
    C --> C2["API ↔ PostgreSQL"]
    C --> C3["Pipeline bout en bout"]
    
    D --> D1["Détection anomalie"]
    D --> D2["Prédiction panne"]
    D --> D3["Gestion données manquantes"]
    D --> D4["Mise à jour modèle"]
```

---

## 2. Stratégie de test — Pyramide des tests

```mermaid
graph TD
    subgraph "Pyramide des tests"
        A["🔺 Tests de recette<br/>(5-10 scénarios métier)<br/>Coût élevé / Confiance élevée"]
        B["🔶 Tests d'intégration<br/>(20-30 tests)<br/>Coût moyen / Confiance moyenne"]
        C["🟩 Tests unitaires<br/>(100+ tests)<br/>Coût faible / Confiance ciblée"]
    end
    C --> B --> A
```

| Niveau | Quantité cible | Couverture | Fréquence d'exécution |
|--------|:--------------:|:----------:|:---------------------:|
| **Unitaires** | 100+ tests | ≥ 80% du code | À chaque commit (CI) |
| **Intégration** | 20-30 tests | Flux critiques | À chaque PR (CI) |
| **Recette** | 5-10 scénarios | Cas d'usage métier | Avant chaque release |
| **Performance** | 3-5 tests | Charge et stress | Hebdomadaire |

---

## 3. Tests unitaires (pytest)

### 3.1 Tests du pipeline de données

#### Validation du schéma de données

```python
# tests/test_data_pipeline.py
import pytest
from app.data.validator import validate_sensor_data

class TestDataValidation:
    """Tests de validation des données capteurs."""
    
    def test_valid_sensor_data(self):
        """Données capteur valides acceptées."""
        data = {
            "machine_id": "LYN-CNC-01",
            "sensor_type": "temperature",
            "value": 72.3,
            "timestamp": "2026-05-30T10:00:00Z"
        }
        assert validate_sensor_data(data) is True

    def test_missing_machine_id(self):
        """Rejet des données sans identifiant machine."""
        data = {
            "sensor_type": "temperature",
            "value": 72.3,
            "timestamp": "2026-05-30T10:00:00Z"
        }
        with pytest.raises(ValueError, match="machine_id requis"):
            validate_sensor_data(data)

    def test_invalid_value_type(self):
        """Rejet des valeurs non numériques."""
        data = {
            "machine_id": "LYN-CNC-01",
            "sensor_type": "temperature",
            "value": "non_numérique",
            "timestamp": "2026-05-30T10:00:00Z"
        }
        with pytest.raises(TypeError):
            validate_sensor_data(data)

    def test_value_out_of_physical_range(self):
        """Rejet des valeurs physiquement impossibles."""
        data = {
            "machine_id": "LYN-CNC-01",
            "sensor_type": "temperature",
            "value": -500.0,  # Impossible
            "timestamp": "2026-05-30T10:00:00Z"
        }
        with pytest.raises(ValueError, match="hors limites"):
            validate_sensor_data(data)
```

#### Nettoyage des données

```python
# tests/test_data_cleaning.py
import pytest
import pandas as pd
import numpy as np
from app.data.cleaning import clean_sensor_data, handle_missing_values

class TestDataCleaning:
    """Tests de nettoyage des données."""

    def test_remove_duplicates(self):
        """Suppression des doublons."""
        df = pd.DataFrame({
            "machine_id": ["M1", "M1", "M2"],
            "timestamp": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "value": [10.0, 10.0, 20.0]
        })
        result = clean_sensor_data(df)
        assert len(result) == 2

    def test_handle_missing_values_interpolation(self):
        """Interpolation linéaire des valeurs manquantes."""
        df = pd.DataFrame({
            "value": [10.0, np.nan, 30.0, np.nan, 50.0]
        })
        result = handle_missing_values(df, method="interpolate")
        assert result["value"].iloc[1] == pytest.approx(20.0)
        assert result["value"].iloc[3] == pytest.approx(40.0)

    def test_outlier_detection(self):
        """Détection des valeurs aberrantes (Z-score > 3)."""
        values = [70, 71, 69, 72, 70, 500]  # 500 = outlier
        df = pd.DataFrame({"value": values})
        result = clean_sensor_data(df)
        assert 500 not in result["value"].values
```

#### Feature engineering

```python
# tests/test_feature_engineering.py
import pytest
import pandas as pd
import numpy as np
from app.ml.features import compute_rolling_features, compute_trend

class TestFeatureEngineering:
    """Tests du feature engineering."""

    def test_rolling_mean(self):
        """Calcul de la moyenne glissante sur 3 périodes."""
        df = pd.DataFrame({"value": [10, 20, 30, 40, 50]})
        result = compute_rolling_features(df, window=3)
        assert result["rolling_mean_3"].iloc[2] == pytest.approx(20.0)
        assert result["rolling_mean_3"].iloc[4] == pytest.approx(40.0)

    def test_rolling_std(self):
        """Calcul de l'écart-type glissant."""
        df = pd.DataFrame({"value": [10, 10, 10, 10]})
        result = compute_rolling_features(df, window=3)
        assert result["rolling_std_3"].iloc[3] == pytest.approx(0.0)

    def test_trend_computation(self):
        """Détection de tendance haussière."""
        df = pd.DataFrame({"value": [10, 20, 30, 40, 50]})
        trend = compute_trend(df["value"])
        assert trend > 0  # Tendance positive
```

### 3.2 Tests des modèles ML

```python
# tests/test_ml_models.py
import pytest
import numpy as np
from sklearn.datasets import make_classification
from app.ml.models import train_random_forest, predict_failure
from app.ml.evaluation import evaluate_model

class TestMLModels:
    """Tests des modèles de machine learning."""

    @pytest.fixture
    def sample_data(self):
        """Jeu de données de test pour les modèles."""
        X, y = make_classification(
            n_samples=1000, n_features=10, 
            n_classes=2, random_state=42
        )
        return X, y

    def test_model_training(self, sample_data):
        """Le modèle s'entraîne sans erreur."""
        X, y = sample_data
        model = train_random_forest(X, y)
        assert model is not None
        assert hasattr(model, "predict")

    def test_prediction_output_shape(self, sample_data):
        """Les prédictions ont la bonne dimension."""
        X, y = sample_data
        model = train_random_forest(X, y)
        predictions = model.predict(X[:10])
        assert predictions.shape == (10,)

    def test_prediction_values_binary(self, sample_data):
        """Les prédictions sont binaires (0 ou 1)."""
        X, y = sample_data
        model = train_random_forest(X, y)
        predictions = model.predict(X)
        assert set(predictions).issubset({0, 1})

    def test_model_accuracy_threshold(self, sample_data):
        """L'accuracy dépasse le seuil minimal de 85%."""
        X, y = sample_data
        model = train_random_forest(X, y)
        metrics = evaluate_model(model, X, y)
        assert metrics["accuracy"] >= 0.85

    def test_model_recall_threshold(self, sample_data):
        """Le recall dépasse le seuil minimal de 90%."""
        X, y = sample_data
        model = train_random_forest(X, y)
        metrics = evaluate_model(model, X, y)
        assert metrics["recall"] >= 0.90

    def test_model_serialization(self, sample_data, tmp_path):
        """Le modèle peut être sérialisé et désérialisé."""
        import joblib
        X, y = sample_data
        model = train_random_forest(X, y)
        path = tmp_path / "model.joblib"
        joblib.dump(model, path)
        loaded_model = joblib.load(path)
        np.testing.assert_array_equal(
            model.predict(X[:5]),
            loaded_model.predict(X[:5])
        )
```

### 3.3 Tests des endpoints API

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

class TestHealthEndpoint:
    """Tests du endpoint /health."""

    def test_health_returns_200(self):
        """Le endpoint /health retourne 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self):
        """Le endpoint /health retourne un statut."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

class TestPredictEndpoint:
    """Tests du endpoint /predict."""

    def test_predict_valid_input(self):
        """Prédiction avec des données valides."""
        payload = {
            "machine_id": "LYN-CNC-01",
            "temperature": 72.3,
            "vibration": 0.45,
            "pressure": 6.2,
            "humidity": 45.0,
            "current": 12.8
        }
        response = client.post("/predict/LYN-CNC-01", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "rul_hours" in data

    def test_predict_missing_field(self):
        """Rejet si champ obligatoire manquant."""
        payload = {"machine_id": "LYN-CNC-01"}
        response = client.post("/predict/LYN-CNC-01", json=payload)
        assert response.status_code == 422  # Validation error

    def test_predict_unknown_machine(self):
        """Machine inconnue retourne 404."""
        payload = {
            "machine_id": "UNKNOWN",
            "temperature": 72.3,
            "vibration": 0.45,
            "pressure": 6.2,
            "humidity": 45.0,
            "current": 12.8
        }
        response = client.post("/predict/UNKNOWN", json=payload)
        assert response.status_code == 404

class TestMachinesEndpoint:
    """Tests du endpoint /machines."""

    def test_list_machines(self):
        """Liste des machines retourne une liste."""
        response = client.get("/machines")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_machine_detail(self):
        """Détail d'une machine existante."""
        response = client.get("/machines/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "code_machine" in data

class TestAlertsEndpoint:
    """Tests du endpoint /alerts."""

    def test_list_alerts(self):
        """Liste des alertes retourne une liste."""
        response = client.get("/alerts")
        assert response.status_code == 200

    def test_acknowledge_alert(self):
        """Acquittement d'une alerte."""
        response = client.put("/alerts/1/acknowledge")
        assert response.status_code in [200, 404]
```

### 3.4 Tests des fonctions utilitaires

```python
# tests/test_utils.py
import pytest
from app.utils.alerts import classify_alert_level, compute_health_score
from app.utils.formatting import format_rul_display

class TestAlertClassification:
    """Tests de classification des niveaux d'alerte."""

    def test_normal_state(self):
        """Machine en état normal = pas d'alerte."""
        assert classify_alert_level(health_score=90) == "normal"

    def test_warning_state(self):
        """Dégradation détectée = alerte préventive."""
        assert classify_alert_level(health_score=55) == "warning"

    def test_critical_state(self):
        """État critique = alerte urgente."""
        assert classify_alert_level(health_score=20) == "critical"

class TestHealthScore:
    """Tests du calcul de score de santé."""

    def test_perfect_health(self):
        """Toutes les valeurs nominales = score élevé."""
        score = compute_health_score(
            temperature=65, vibration=0.2,
            pressure=6.0, current=10.0
        )
        assert score >= 80

    def test_degraded_health(self):
        """Valeurs dégradées = score moyen."""
        score = compute_health_score(
            temperature=95, vibration=0.8,
            pressure=8.5, current=18.0
        )
        assert 30 <= score <= 70

class TestFormatting:
    """Tests de formatage d'affichage."""

    def test_format_rul_hours(self):
        """Formatage RUL en heures."""
        assert format_rul_display(48) == "2 jours"

    def test_format_rul_minutes(self):
        """Formatage RUL < 1h."""
        assert format_rul_display(0.5) == "30 minutes"
```

---

## 4. Tests d'intégration

### 4.1 API ↔ Modèle ML

| ID Test | Description | Entrée | Résultat attendu |
|---------|-------------|--------|-----------------|
| INT-01 | L'API appelle correctement le modèle ML | Données capteurs valides via POST /predict | Prédiction retournée avec score de confiance |
| INT-02 | Rechargement du modèle à chaud | Nouveau fichier modèle .joblib | API utilise le nouveau modèle sans redémarrage |
| INT-03 | Gestion de l'absence du modèle | Fichier modèle supprimé | Erreur 503 avec message explicite |
| INT-04 | Cohérence des features | Features API ≠ features modèle | Erreur 400 avec détail des features manquantes |

### 4.2 API ↔ Base de données PostgreSQL

| ID Test | Description | Entrée | Résultat attendu |
|---------|-------------|--------|-----------------|
| INT-05 | Lecture des machines | GET /machines | Liste complète depuis la BDD |
| INT-06 | Écriture des prédictions | POST /predict | Prédiction sauvegardée en BDD |
| INT-07 | Lecture des alertes avec filtres | GET /alerts?niveau=critical | Seules les alertes critiques |
| INT-08 | Connexion BDD perdue | PostgreSQL arrêté | Erreur 503, reconnexion automatique |
| INT-09 | Migrations BDD | Nouveau schéma | Migration appliquée sans perte de données |

### 4.3 Pipeline bout en bout

```python
# tests/integration/test_pipeline_e2e.py
import pytest
import time

class TestEndToEndPipeline:
    """Tests du pipeline complet : données brutes → prédiction → alerte."""

    def test_full_pipeline_normal_data(self, docker_compose_env):
        """Pipeline complet avec données normales."""
        # 1. Injecter des données capteurs via MQTT
        publish_sensor_data("LYN-CNC-01", temperature=70, vibration=0.3)
        time.sleep(5)  # Attendre l'ingestion
        
        # 2. Vérifier l'insertion en BDD
        count = db_query("SELECT COUNT(*) FROM mesures WHERE machine_id=1")
        assert count > 0
        
        # 3. Lancer la prédiction
        response = api_client.post("/predict/LYN-CNC-01")
        assert response.status_code == 200
        assert response.json()["prediction"] == "normal"
        
        # 4. Vérifier qu'aucune alerte n'est générée
        alerts = db_query("SELECT COUNT(*) FROM alertes WHERE machine_id=1 AND statut='active'")
        assert alerts == 0

    def test_full_pipeline_anomaly_data(self, docker_compose_env):
        """Pipeline complet avec données anormales → alerte générée."""
        # 1. Injecter des données anormales
        publish_sensor_data("LYN-CNC-01", temperature=120, vibration=2.5)
        time.sleep(5)
        
        # 2. Lancer la prédiction
        response = api_client.post("/predict/LYN-CNC-01")
        assert response.status_code == 200
        assert response.json()["prediction"] == "failure_imminent"
        
        # 3. Vérifier la génération d'alerte
        alerts = db_query(
            "SELECT * FROM alertes WHERE machine_id=1 AND statut='active'"
        )
        assert len(alerts) >= 1
        assert alerts[0]["niveau"] in ["warning", "critical"]
```

### 4.4 Tests avec Docker Compose

```yaml
# docker-compose.test.yml
version: "3.8"
services:
  test-db:
    image: postgres:16
    environment:
      POSTGRES_DB: mecha_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
  
  test-api:
    build: .
    environment:
      DATABASE_URL: postgresql://test:test@test-db:5432/mecha_test
      MODEL_PATH: /app/models/test_model.joblib
    depends_on:
      - test-db
    ports:
      - "8001:8000"
```

---

## 5. Tests de recette — Scénarios métier

### Scénario 1 : Détection d'une anomalie de vibration

| Élément | Détail |
|---------|--------|
| **ID** | REC-01 |
| **Objectif** | Vérifier qu'une vibration anormale déclenche une alerte |
| **Prérequis** | Machine LYN-CNC-01 en fonctionnement normal depuis > 24h |
| **Données d'entrée** | Vibration passant de 0.3 mm/s à 2.5 mm/s progressivement sur 2h |
| **Résultat attendu** | Alerte préventive générée quand vibration > seuil (1.5 mm/s) |
| **Critère de succès** | Alerte visible sur le dashboard dans un délai < 5 minutes |
| **Vérifié par** | Responsable maintenance (validation métier) |

### Scénario 2 : Prédiction de panne dans 48h

| Élément | Détail |
|---------|--------|
| **ID** | REC-02 |
| **Objectif** | Vérifier la notification de panne imminente |
| **Prérequis** | Modèle entraîné avec historique > 30 jours |
| **Données d'entrée** | Dégradation progressive : température +15°C, vibration ×3, courant +20% sur 7 jours |
| **Résultat attendu** | Prédiction RUL < 48h, alerte urgente (rouge), notification envoyée |
| **Critère de succès** | RUL estimé entre 24h et 72h (marge ±50%) |
| **Vérifié par** | Équipe data + Responsable maintenance |

### Scénario 3 : Machine en état normal — Pas de fausse alerte

| Élément | Détail |
|---------|--------|
| **ID** | REC-03 |
| **Objectif** | Vérifier l'absence de fausse alerte en conditions normales |
| **Prérequis** | Machine fonctionnant dans les plages nominales |
| **Données d'entrée** | 7 jours de données normales (toutes valeurs dans les seuils) |
| **Résultat attendu** | Aucune alerte générée, score de santé > 80% |
| **Critère de succès** | 0 fausse alerte sur la période de test |
| **Vérifié par** | Équipe data |

### Scénario 4 : Données capteur manquantes

| Élément | Détail |
|---------|--------|
| **ID** | REC-04 |
| **Objectif** | Vérifier la gestion gracieuse des données manquantes |
| **Prérequis** | Machine en fonctionnement |
| **Données d'entrée** | Capteur de température déconnecté pendant 2h |
| **Résultat attendu** | Alerte technique « capteur indisponible », prédiction suspendue ou dégradée |
| **Critère de succès** | Pas de crash système, message informatif à l'utilisateur |
| **Vérifié par** | Équipe technique |

### Scénario 5 : Mise à jour du modèle sans régression

| Élément | Détail |
|---------|--------|
| **ID** | REC-05 |
| **Objectif** | Vérifier qu'une mise à jour du modèle n'entraîne pas de régression |
| **Prérequis** | Modèle v1 en production, modèle v2 entraîné |
| **Données d'entrée** | Même jeu de données de référence (100 cas annotés) |
| **Résultat attendu** | Métriques v2 ≥ métriques v1 (accuracy, recall, F1) |
| **Critère de succès** | Aucune métrique ne baisse de plus de 2% |
| **Vérifié par** | Équipe data |

---

## 6. Jeux de données de test

### 6.1 Description des jeux de données

| Jeu de données | Description | Volume | Usage |
|----------------|-------------|--------|-------|
| `dataset_normal.csv` | Données de fonctionnement nominal | 10 000 mesures | Tests unitaires, baseline |
| `dataset_anomalies.csv` | Données avec anomalies connues et annotées | 2 000 mesures | Validation du modèle ML |
| `dataset_degraded.csv` | Données avec valeurs manquantes et outliers | 5 000 mesures | Tests de robustesse |
| `dataset_stress.csv` | Volume important de données | 1 000 000 mesures | Tests de performance |
| `dataset_edge_cases.csv` | Cas limites (valeurs aux bornes des seuils) | 500 mesures | Tests de régression |

### 6.2 Structure des jeux de données

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `machine_id` | string | Identifiant machine | LYN-CNC-01 |
| `timestamp` | datetime | Horodatage de la mesure | 2026-05-30T10:00:00Z |
| `temperature` | float | Température (°C) | 72.3 |
| `vibration` | float | Vibration (mm/s) | 0.45 |
| `pressure` | float | Pression (bar) | 6.2 |
| `humidity` | float | Humidité (%) | 45.0 |
| `current` | float | Courant (A) | 12.8 |
| `label` | int | Étiquette (0=normal, 1=panne) | 0 |

---

## 7. Matrice de traçabilité

| Exigence | Description | Tests associés | Priorité |
|----------|-------------|---------------|----------|
| EX-01 | Collecter les données capteurs en temps réel | INT-05, REC-04 | Haute |
| EX-02 | Prédire les pannes avec une accuracy ≥ 85% | TU-ML-04, REC-02 | Haute |
| EX-03 | Générer des alertes en < 5 minutes | REC-01, REC-02 | Haute |
| EX-04 | Afficher le score de santé machine | TU-UTIL-02, REC-03 | Moyenne |
| EX-05 | Estimer le RUL avec une MAE ≤ 24h | TU-ML-05, REC-02 | Haute |
| EX-06 | API disponible 99.5% du temps | INT-08, PERF-01 | Haute |
| EX-07 | Pas de fausse alerte en conditions normales | REC-03 | Haute |
| EX-08 | Gestion des données manquantes | TU-DATA-03, REC-04 | Moyenne |
| EX-09 | Mise à jour modèle sans régression | REC-05, INT-02 | Moyenne |
| EX-10 | Temps de réponse API < 500ms | PERF-02 | Moyenne |

---

## 8. Critères d'acceptation et seuils

### 8.1 Métriques du modèle ML

| Métrique | Seuil minimum | Seuil cible | Description |
|----------|:------------:|:-----------:|-------------|
| **Accuracy** | ≥ 85% | ≥ 90% | Taux de prédictions correctes |
| **Precision** | ≥ 85% | ≥ 90% | Taux de vrais positifs parmi les positifs prédits |
| **Recall** | ≥ 90% | ≥ 95% | Taux de pannes réelles détectées (critique) |
| **F1-Score** | ≥ 87% | ≥ 92% | Moyenne harmonique precision/recall |
| **MAE (RUL)** | ≤ 24h | ≤ 12h | Erreur moyenne absolue sur le RUL |
| **R² (RUL)** | ≥ 0.80 | ≥ 0.90 | Coefficient de détermination |

> ⚠️ **Le recall est la métrique prioritaire** : il est plus grave de manquer une panne (faux négatif) que de générer une fausse alerte (faux positif).

### 8.2 Métriques de performance

| Métrique | Seuil | Conditions |
|----------|:-----:|-----------|
| Temps de réponse API (P95) | < 500ms | Charge normale (10 req/s) |
| Temps de réponse API (P99) | < 1s | Charge élevée (50 req/s) |
| Disponibilité API | ≥ 99.5% | Sur 30 jours glissants |
| Temps d'ingestion (capteur → BDD) | < 5s | Par mesure individuelle |
| Temps de prédiction (inférence) | < 200ms | Par machine |

### 8.3 Couverture de code

| Composant | Couverture minimale |
|-----------|:-------------------:|
| Pipeline de données | ≥ 80% |
| Modèles ML | ≥ 75% |
| API FastAPI | ≥ 85% |
| Fonctions utilitaires | ≥ 90% |
| **Global** | **≥ 80%** |

---

## 9. Outils de testing

| Outil | Usage | Version |
|-------|-------|---------|
| **pytest** | Framework de test principal | ≥ 7.0 |
| **pytest-cov** | Couverture de code | ≥ 4.0 |
| **httpx** | Client HTTP pour tests API (async) | ≥ 0.24 |
| **pytest-asyncio** | Support tests asynchrones | ≥ 0.21 |
| **locust** | Tests de charge et performance | ≥ 2.0 |
| **factory-boy** | Génération de données de test | ≥ 3.0 |
| **Docker Compose** | Environnement d'intégration | ≥ 2.0 |
| **GitHub Actions** | Exécution automatisée CI | — |
| **SonarQube** | Analyse qualité code (optionnel) | — |

### Configuration pytest

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Tests unitaires
    integration: Tests d'intégration
    recette: Tests de recette métier
    slow: Tests lents (> 30s)
```

---

## 10. Planning des tests

```mermaid
gantt
    title Planning des tests MECHA Predict
    dateFormat  YYYY-MM-DD
    section Tests Unitaires
    Rédaction tests pipeline      :t1, 2026-06-01, 5d
    Rédaction tests ML            :t2, 2026-06-01, 5d
    Rédaction tests API           :t3, 2026-06-06, 5d
    Exécution et correction       :t4, 2026-06-11, 5d
    section Tests Intégration
    Configuration Docker tests    :t5, 2026-06-11, 3d
    Rédaction tests intégration   :t6, 2026-06-14, 5d
    Exécution et correction       :t7, 2026-06-19, 5d
    section Tests Recette
    Préparation jeux de données   :t8, 2026-06-19, 3d
    Exécution scénarios métier    :t9, 2026-06-22, 5d
    Validation avec métier        :t10, 2026-06-27, 3d
    section Tests Performance
    Configuration Locust          :t11, 2026-06-27, 2d
    Exécution tests charge        :t12, 2026-06-29, 3d
    section Rapport
    Rédaction rapport final       :t13, 2026-07-02, 3d
```

### Responsabilités

| Responsable | Tests assignés |
|-------------|---------------|
| **Malek El Fayedh** | Tests pipeline données, tests d'intégration BDD |
| **Thibaut Doreau** | Tests modèles ML, tests de performance |
| **Vincent Gonçalves** | Tests API, tests d'intégration API↔ML |
| **Pierre-Louis Guinel** | Tests de recette, coordination avec le métier |

---

## 11. Rapport de test — Template

### Informations générales

| Champ | Valeur |
|-------|--------|
| **Date d'exécution** | JJ/MM/AAAA |
| **Version testée** | vX.Y.Z |
| **Environnement** | Développement / Staging / Production |
| **Exécuté par** | Nom |

### Résumé

| Catégorie | Total | Passés ✅ | Échoués ❌ | Ignorés ⏭️ |
|-----------|:-----:|:---------:|:----------:|:-----------:|
| Unitaires | — | — | — | — |
| Intégration | — | — | — | — |
| Recette | — | — | — | — |
| Performance | — | — | — | — |
| **Total** | **—** | **—** | **—** | **—** |

### Couverture de code

| Composant | Couverture | Objectif | Statut |
|-----------|:----------:|:--------:|:------:|
| Pipeline données | —% | ≥ 80% | ✅/❌ |
| Modèles ML | —% | ≥ 75% | ✅/❌ |
| API | —% | ≥ 85% | ✅/❌ |
| Utilitaires | —% | ≥ 90% | ✅/❌ |

### Anomalies détectées

| ID | Sévérité | Description | Statut | Assigné à |
|----|----------|-------------|--------|-----------|
| — | Critique/Majeur/Mineur | — | Ouvert/Résolu | — |

### Décision

- [ ] ✅ **GO** — Tous les critères d'acceptation sont satisfaits
- [ ] ❌ **NO-GO** — Des anomalies bloquantes subsistent

---

> **Document validé par** : Équipe projet MECHA  
> **Prochaine révision** : Après exécution des premiers tests
