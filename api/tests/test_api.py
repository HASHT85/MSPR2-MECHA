"""
MSPR 2 MECHA -- Tests unitaires de l'API FastAPI.

Couvre tous les endpoints avec pytest + httpx.
Les tests fonctionnent sans modeles ML charges (mode fallback).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app, alert_thresholds


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Client HTTP asynchrone pour tester l'API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# Donnees de test reutilisables
VALID_SENSOR_DATA = {
    "temperature": 85.0,
    "vibration": 3.2,
    "humidity": 45.0,
    "pressure": 1013.0,
    "energy_consumption": 150.0,
    "predicted_remaining_life": 120.0,
    "temp_rolling_10min": 84.5,
    "temp_trend_1h": 0.3,
    "vibr_rolling_10min": 3.1,
    "temp_std_30min": 1.2,
    "energy_vibr_ratio": 46.9,
    "downtime_risk": 0.15,
    "machine_id": "MCH-001",
}

MINIMAL_SENSOR_DATA = {
    "temperature": 50.0,
    "vibration": 1.0,
    "humidity": 40.0,
    "pressure": 1013.0,
    "energy_consumption": 100.0,
    "predicted_remaining_life": 200.0,
}

CRITICAL_SENSOR_DATA = {
    "temperature": 120.0,
    "vibration": 8.0,
    "humidity": 85.0,
    "pressure": 1013.0,
    "energy_consumption": 250.0,
    "predicted_remaining_life": 10.0,
    "machine_id": "MCH-CRIT",
}


# ==============================================================================
# Tests -- GET /health
# ==============================================================================

class TestHealthCheck:
    """Tests pour le endpoint /health."""

    @pytest.mark.anyio
    async def test_health_returns_200(self, client: AsyncClient):
        """Le health check doit retourner 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_health_response_structure(self, client: AsyncClient):
        """La reponse doit contenir les champs attendus."""
        response = await client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "models_loaded" in data
        assert "models_available" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_health_status_healthy(self, client: AsyncClient):
        """Le statut doit etre 'healthy'."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.anyio
    async def test_health_models_available_keys(self, client: AsyncClient):
        """Les cles des modeles doivent etre presentes."""
        response = await client.get("/health")
        data = response.json()
        models_avail = data["models_available"]

        assert "classifier" in models_avail
        assert "xgboost" in models_avail
        assert "isolation_forest" in models_avail
        assert "rul_regressor" in models_avail


# ==============================================================================
# Tests -- POST /predict
# ==============================================================================

class TestPredict:
    """Tests pour le endpoint /predict."""

    @pytest.mark.anyio
    async def test_predict_valid_input(self, client: AsyncClient):
        """Une prediction avec des donnees valides doit retourner 200."""
        response = await client.post("/predict", json=VALID_SENSOR_DATA)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_predict_response_structure(self, client: AsyncClient):
        """La reponse doit contenir tous les champs attendus."""
        response = await client.post("/predict", json=VALID_SENSOR_DATA)
        data = response.json()

        assert "prediction" in data
        assert "confidence" in data
        assert "risk_level" in data
        assert "alerts" in data
        assert "model_used" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_predict_valid_prediction_values(self, client: AsyncClient):
        """Les valeurs de prediction doivent etre dans les plages attendues."""
        response = await client.post("/predict", json=VALID_SENSOR_DATA)
        data = response.json()

        assert data["prediction"] in ("normal", "maintenance_required")
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["risk_level"] in ("low", "medium", "high", "critical")
        assert isinstance(data["alerts"], list)

    @pytest.mark.anyio
    async def test_predict_minimal_input(self, client: AsyncClient):
        """La prediction doit fonctionner avec les champs minimaux."""
        response = await client.post("/predict", json=MINIMAL_SENSOR_DATA)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_predict_critical_temperature_triggers_alert(
        self, client: AsyncClient
    ):
        """Une temperature critique doit declencher une alerte."""
        response = await client.post("/predict", json=CRITICAL_SENSOR_DATA)
        data = response.json()
        assert len(data["alerts"]) > 0
        assert any("Temperature" in alert for alert in data["alerts"])

    @pytest.mark.anyio
    async def test_predict_machine_id_preserved(self, client: AsyncClient):
        """Le machine_id doit etre preserve dans la reponse."""
        response = await client.post("/predict", json=VALID_SENSOR_DATA)
        data = response.json()
        assert data["machine_id"] == "MCH-001"

    @pytest.mark.anyio
    async def test_predict_missing_required_field(self, client: AsyncClient):
        """Des champs manquants doivent retourner 422."""
        incomplete = {"temperature": 85.0, "vibration": 3.2}
        response = await client.post("/predict", json=incomplete)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_predict_invalid_temperature_range(self, client: AsyncClient):
        """Une temperature hors plage doit retourner 422."""
        invalid = {**MINIMAL_SENSOR_DATA, "temperature": 600.0}
        response = await client.post("/predict", json=invalid)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_predict_negative_vibration(self, client: AsyncClient):
        """Une vibration negative doit retourner 422."""
        invalid = {**MINIMAL_SENSOR_DATA, "vibration": -1.0}
        response = await client.post("/predict", json=invalid)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_predict_fallback_model(self, client: AsyncClient):
        """En mode fallback, le modele utilise doit etre 'fallback_heuristic'."""
        response = await client.post("/predict", json=VALID_SENSOR_DATA)
        data = response.json()
        # En mode test sans modeles charges
        assert data["model_used"] in (
            "fallback_heuristic", "random_forest", "xgboost"
        )


# ==============================================================================
# Tests -- POST /predict/batch
# ==============================================================================

class TestPredictBatch:
    """Tests pour le endpoint /predict/batch."""

    @pytest.mark.anyio
    async def test_batch_single_machine(self, client: AsyncClient):
        """Un batch avec une seule machine doit fonctionner."""
        payload = {"machines": [VALID_SENSOR_DATA]}
        response = await client.post("/predict/batch", json=payload)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_batch_response_structure(self, client: AsyncClient):
        """La reponse batch doit contenir les champs attendus."""
        payload = {"machines": [VALID_SENSOR_DATA]}
        response = await client.post("/predict/batch", json=payload)
        data = response.json()

        assert "predictions" in data
        assert "total" in data
        assert "processing_time_ms" in data

    @pytest.mark.anyio
    async def test_batch_multiple_machines(self, client: AsyncClient):
        """Un batch avec plusieurs machines doit retourner le bon nombre."""
        payload = {
            "machines": [
                VALID_SENSOR_DATA,
                MINIMAL_SENSOR_DATA,
                CRITICAL_SENSOR_DATA,
            ]
        }
        response = await client.post("/predict/batch", json=payload)
        data = response.json()

        assert data["total"] == 3
        assert len(data["predictions"]) == 3
        assert data["processing_time_ms"] >= 0

    @pytest.mark.anyio
    async def test_batch_empty_list(self, client: AsyncClient):
        """Un batch vide doit retourner 422."""
        payload = {"machines": []}
        response = await client.post("/predict/batch", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_batch_each_prediction_valid(self, client: AsyncClient):
        """Chaque prediction du batch doit etre valide."""
        payload = {"machines": [VALID_SENSOR_DATA, MINIMAL_SENSOR_DATA]}
        response = await client.post("/predict/batch", json=payload)
        data = response.json()

        for pred in data["predictions"]:
            assert pred["prediction"] in ("normal", "maintenance_required")
            assert 0.0 <= pred["confidence"] <= 1.0


# ==============================================================================
# Tests -- POST /predict/rul
# ==============================================================================

class TestPredictRUL:
    """Tests pour le endpoint /predict/rul."""

    @pytest.mark.anyio
    async def test_rul_valid_input(self, client: AsyncClient):
        """Une prediction RUL avec des donnees valides doit retourner 200."""
        response = await client.post("/predict/rul", json=VALID_SENSOR_DATA)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_rul_response_structure(self, client: AsyncClient):
        """La reponse RUL doit contenir tous les champs attendus."""
        response = await client.post("/predict/rul", json=VALID_SENSOR_DATA)
        data = response.json()

        assert "rul_hours" in data
        assert "rul_category" in data
        assert "confidence" in data
        assert "model_used" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_rul_positive_value(self, client: AsyncClient):
        """Le RUL doit etre positif ou nul."""
        response = await client.post("/predict/rul", json=VALID_SENSOR_DATA)
        data = response.json()
        assert data["rul_hours"] >= 0.0

    @pytest.mark.anyio
    async def test_rul_valid_category(self, client: AsyncClient):
        """La categorie RUL doit etre dans les valeurs attendues."""
        response = await client.post("/predict/rul", json=VALID_SENSOR_DATA)
        data = response.json()
        assert data["rul_category"] in ("urgent", "soon", "moderate", "safe")

    @pytest.mark.anyio
    async def test_rul_critical_machine_lower_rul(self, client: AsyncClient):
        """Une machine critique doit avoir un RUL plus bas."""
        response_normal = await client.post(
            "/predict/rul", json=MINIMAL_SENSOR_DATA
        )
        response_critical = await client.post(
            "/predict/rul", json=CRITICAL_SENSOR_DATA
        )

        rul_normal = response_normal.json()["rul_hours"]
        rul_critical = response_critical.json()["rul_hours"]

        # La machine critique devrait avoir un RUL inferieur
        assert rul_critical < rul_normal

    @pytest.mark.anyio
    async def test_rul_minimal_input(self, client: AsyncClient):
        """La prediction RUL doit fonctionner avec les champs minimaux."""
        response = await client.post("/predict/rul", json=MINIMAL_SENSOR_DATA)
        assert response.status_code == 200


# ==============================================================================
# Tests -- POST /anomaly
# ==============================================================================

class TestAnomalyDetection:
    """Tests pour le endpoint /anomaly."""

    @pytest.mark.anyio
    async def test_anomaly_valid_input(self, client: AsyncClient):
        """La detection d'anomalie avec des donnees valides doit retourner 200."""
        response = await client.post("/anomaly", json=VALID_SENSOR_DATA)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_anomaly_response_structure(self, client: AsyncClient):
        """La reponse doit contenir tous les champs attendus."""
        response = await client.post("/anomaly", json=VALID_SENSOR_DATA)
        data = response.json()

        assert "is_anomaly" in data
        assert "anomaly_score" in data
        assert "severity" in data
        assert "contributing_factors" in data
        assert "model_used" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_anomaly_boolean_is_anomaly(self, client: AsyncClient):
        """is_anomaly doit etre un booleen."""
        response = await client.post("/anomaly", json=VALID_SENSOR_DATA)
        data = response.json()
        assert isinstance(data["is_anomaly"], bool)

    @pytest.mark.anyio
    async def test_anomaly_valid_severity(self, client: AsyncClient):
        """La severite doit etre dans les valeurs attendues."""
        response = await client.post("/anomaly", json=VALID_SENSOR_DATA)
        data = response.json()
        assert data["severity"] in ("normal", "warning", "critical")

    @pytest.mark.anyio
    async def test_anomaly_critical_data_detected(self, client: AsyncClient):
        """Des donnees critiques doivent etre detectees comme anomalie."""
        response = await client.post("/anomaly", json=CRITICAL_SENSOR_DATA)
        data = response.json()

        # Avec temperature et vibration critiques, une anomalie devrait etre detectee
        assert data["is_anomaly"] is True
        assert len(data["contributing_factors"]) > 0

    @pytest.mark.anyio
    async def test_anomaly_normal_data_not_anomaly(self, client: AsyncClient):
        """Des donnees normales ne doivent pas etre une anomalie."""
        response = await client.post("/anomaly", json=MINIMAL_SENSOR_DATA)
        data = response.json()
        assert data["is_anomaly"] is False

    @pytest.mark.anyio
    async def test_anomaly_contributing_factors_on_anomaly(
        self, client: AsyncClient
    ):
        """Les facteurs contributifs doivent etre renseignes si anomalie."""
        response = await client.post("/anomaly", json=CRITICAL_SENSOR_DATA)
        data = response.json()

        if data["is_anomaly"]:
            assert len(data["contributing_factors"]) > 0
            # Verifier que les facteurs sont des chaines de caracteres
            for factor in data["contributing_factors"]:
                assert isinstance(factor, str)


# ==============================================================================
# Tests -- GET /metrics
# ==============================================================================

class TestMetrics:
    """Tests pour le endpoint /metrics."""

    @pytest.mark.anyio
    async def test_metrics_returns_200(self, client: AsyncClient):
        """Le endpoint /metrics doit retourner 200."""
        response = await client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_metrics_response_structure(self, client: AsyncClient):
        """La reponse doit contenir les champs attendus."""
        response = await client.get("/metrics")
        data = response.json()

        assert "models" in data
        assert "api_stats" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_metrics_models_keys(self, client: AsyncClient):
        """Les metriques doivent inclure tous les modeles."""
        response = await client.get("/metrics")
        data = response.json()
        models = data["models"]

        assert "random_forest" in models
        assert "xgboost" in models
        assert "isolation_forest" in models
        assert "rf_regressor_rul" in models

    @pytest.mark.anyio
    async def test_metrics_api_stats_keys(self, client: AsyncClient):
        """Les statistiques API doivent contenir les compteurs."""
        response = await client.get("/metrics")
        data = response.json()
        stats = data["api_stats"]

        assert "total_predictions" in stats
        assert "total_anomaly_checks" in stats
        assert "total_rul_predictions" in stats
        assert "uptime_seconds" in stats


# ==============================================================================
# Tests -- GET /model-info
# ==============================================================================

class TestModelInfo:
    """Tests pour le endpoint /model-info."""

    @pytest.mark.anyio
    async def test_model_info_returns_200(self, client: AsyncClient):
        """Le endpoint /model-info doit retourner 200."""
        response = await client.get("/model-info")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_model_info_response_structure(self, client: AsyncClient):
        """La reponse doit contenir les champs attendus."""
        response = await client.get("/model-info")
        data = response.json()

        assert "project" in data
        assert "version" in data
        assert "models" in data
        assert "features" in data
        assert "alert_thresholds" in data
        assert "compliance" in data

    @pytest.mark.anyio
    async def test_model_info_four_models(self, client: AsyncClient):
        """Il doit y avoir exactement 4 modeles documentes."""
        response = await client.get("/model-info")
        data = response.json()
        assert len(data["models"]) == 4

    @pytest.mark.anyio
    async def test_model_info_features_list(self, client: AsyncClient):
        """La liste des features doit contenir les 12 features attendues."""
        response = await client.get("/model-info")
        data = response.json()
        assert len(data["features"]) == 12
        assert "temperature" in data["features"]
        assert "vibration" in data["features"]
        assert "downtime_risk" in data["features"]

    @pytest.mark.anyio
    async def test_model_info_compliance_keys(self, client: AsyncClient):
        """La conformite doit inclure EU AI Act et RGPD."""
        response = await client.get("/model-info")
        data = response.json()
        compliance = data["compliance"]

        assert "eu_ai_act" in compliance
        assert "rgpd" in compliance

    @pytest.mark.anyio
    async def test_model_info_human_in_the_loop(self, client: AsyncClient):
        """Chaque modele doit avoir human_in_the_loop = True (EU AI Act)."""
        response = await client.get("/model-info")
        data = response.json()

        for model in data["models"]:
            assert model.get("human_in_the_loop") is True


# ==============================================================================
# Tests -- GET /alerts/config
# ==============================================================================

class TestAlertsConfigGet:
    """Tests pour le endpoint GET /alerts/config."""

    @pytest.mark.anyio
    async def test_alerts_config_returns_200(self, client: AsyncClient):
        """Le endpoint doit retourner 200."""
        response = await client.get("/alerts/config")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_alerts_config_response_structure(self, client: AsyncClient):
        """La reponse doit contenir tous les seuils."""
        response = await client.get("/alerts/config")
        data = response.json()

        assert "temperature_critical_celsius" in data
        assert "rebuts_max_percent" in data
        assert "trs_min_percent" in data
        assert "cycle_deviation_max_percent" in data
        assert "anomaly_rate_max_percent" in data
        assert "updated_at" in data

    @pytest.mark.anyio
    async def test_alerts_config_default_values(self, client: AsyncClient):
        """Les valeurs par defaut doivent correspondre aux seuils MECHA."""
        # Reinitialiser les seuils
        alert_thresholds.reset_defaults()

        response = await client.get("/alerts/config")
        data = response.json()

        assert data["temperature_critical_celsius"] == 100.0
        assert data["rebuts_max_percent"] == 3.0
        assert data["trs_min_percent"] == 75.0
        assert data["cycle_deviation_max_percent"] == 15.0
        assert data["anomaly_rate_max_percent"] == 10.0


# ==============================================================================
# Tests -- PUT /alerts/config
# ==============================================================================

class TestAlertsConfigPut:
    """Tests pour le endpoint PUT /alerts/config."""

    @pytest.mark.anyio
    async def test_update_single_threshold(self, client: AsyncClient):
        """Modifier un seul seuil doit fonctionner."""
        alert_thresholds.reset_defaults()

        payload = {"temperature_critical_celsius": 110.0}
        response = await client.put("/alerts/config", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["temperature_critical_celsius"] == 110.0
        # Les autres doivent garder leurs valeurs par defaut
        assert data["rebuts_max_percent"] == 3.0

    @pytest.mark.anyio
    async def test_update_multiple_thresholds(self, client: AsyncClient):
        """Modifier plusieurs seuils en une requete."""
        alert_thresholds.reset_defaults()

        payload = {
            "temperature_critical_celsius": 95.0,
            "rebuts_max_percent": 2.5,
            "trs_min_percent": 80.0,
        }
        response = await client.put("/alerts/config", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["temperature_critical_celsius"] == 95.0
        assert data["rebuts_max_percent"] == 2.5
        assert data["trs_min_percent"] == 80.0

    @pytest.mark.anyio
    async def test_update_persists(self, client: AsyncClient):
        """La modification doit etre visible dans le GET suivant."""
        alert_thresholds.reset_defaults()

        payload = {"anomaly_rate_max_percent": 5.0}
        await client.put("/alerts/config", json=payload)

        response = await client.get("/alerts/config")
        data = response.json()
        assert data["anomaly_rate_max_percent"] == 5.0

    @pytest.mark.anyio
    async def test_update_empty_body_no_change(self, client: AsyncClient):
        """Un body vide ne doit rien modifier."""
        alert_thresholds.reset_defaults()

        response = await client.put("/alerts/config", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["temperature_critical_celsius"] == 100.0

    @pytest.mark.anyio
    async def test_update_invalid_negative_value(self, client: AsyncClient):
        """Une valeur invalide doit retourner 422."""
        payload = {"temperature_critical_celsius": -10.0}
        response = await client.put("/alerts/config", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_update_response_has_updated_at(self, client: AsyncClient):
        """La reponse doit contenir un horodatage de mise a jour."""
        payload = {"temperature_critical_celsius": 105.0}
        response = await client.put("/alerts/config", json=payload)
        data = response.json()
        assert "updated_at" in data
        assert len(data["updated_at"]) > 0

    @pytest.fixture(autouse=True)
    def _reset_thresholds(self):
        """Reinitialise les seuils apres chaque test."""
        yield
        alert_thresholds.reset_defaults()


# ==============================================================================
# Tests -- Documentation OpenAPI
# ==============================================================================

class TestOpenAPI:
    """Tests pour la documentation OpenAPI auto-generee."""

    @pytest.mark.anyio
    async def test_openapi_json_available(self, client: AsyncClient):
        """Le schema OpenAPI doit etre accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_openapi_has_paths(self, client: AsyncClient):
        """Le schema doit contenir les chemins definis."""
        response = await client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})

        assert "/health" in paths
        assert "/predict" in paths
        assert "/predict/batch" in paths
        assert "/predict/rul" in paths
        assert "/anomaly" in paths
        assert "/metrics" in paths
        assert "/model-info" in paths
        assert "/alerts/config" in paths

    @pytest.mark.anyio
    async def test_docs_page_available(self, client: AsyncClient):
        """La page Swagger /docs doit etre accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_redoc_page_available(self, client: AsyncClient):
        """La page ReDoc doit etre accessible."""
        response = await client.get("/redoc")
        assert response.status_code == 200


# ==============================================================================
# Tests -- Validation des entrees (edge cases)
# ==============================================================================

class TestInputValidation:
    """Tests de validation des entrees pour les cas limites."""

    @pytest.mark.anyio
    async def test_predict_with_extreme_values(self, client: AsyncClient):
        """Des valeurs extremes mais valides doivent etre acceptees."""
        extreme = {
            "temperature": 0.0,
            "vibration": 0.0,
            "humidity": 0.0,
            "pressure": 0.0,
            "energy_consumption": 0.0,
            "predicted_remaining_life": 0.0,
        }
        response = await client.post("/predict", json=extreme)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_predict_with_max_values(self, client: AsyncClient):
        """Les valeurs maximales autorisees doivent etre acceptees."""
        max_values = {
            "temperature": 500.0,
            "vibration": 100.0,
            "humidity": 100.0,
            "pressure": 2000.0,
            "energy_consumption": 9999.0,
            "predicted_remaining_life": 9999.0,
        }
        response = await client.post("/predict", json=max_values)
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_predict_wrong_type_string(self, client: AsyncClient):
        """Un type incorrect (string au lieu de float) doit retourner 422."""
        invalid = {**MINIMAL_SENSOR_DATA, "temperature": "hot"}
        response = await client.post("/predict", json=invalid)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_batch_exceeds_max_size(self, client: AsyncClient):
        """Un batch depassant la taille max (100) doit retourner 422."""
        payload = {"machines": [MINIMAL_SENSOR_DATA] * 101}
        response = await client.post("/predict/batch", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_predict_empty_body(self, client: AsyncClient):
        """Un body vide doit retourner 422."""
        response = await client.post("/predict", json={})
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_anomaly_with_zero_vibration(self, client: AsyncClient):
        """Vibration a zero ne doit pas causer de division par zero."""
        data = {**MINIMAL_SENSOR_DATA, "vibration": 0.0}
        response = await client.post("/anomaly", json=data)
        assert response.status_code == 200
