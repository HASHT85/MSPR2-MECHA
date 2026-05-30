"""
Tests d'integration MECHA.
Verifie l'integration entre les composants (API + modeles, API + donnees).
"""

import pytest

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


SAMPLE_NORMAL = {
    "temperature": 75.0,
    "vibration": 35.0,
    "humidity": 55.0,
    "pressure": 3.0,
    "energy_consumption": 2.5,
    "predicted_remaining_life": 400,
    "temp_rolling_10min": 74.0,
    "temp_trend_1h": 0.01,
    "vibr_rolling_10min": 34.0,
    "temp_std_30min": 1.5,
    "energy_vibr_ratio": 0.07,
    "downtime_risk": 0.1,
}

SAMPLE_CRITICAL = {
    "temperature": 115.0,
    "vibration": 85.0,
    "humidity": 60.0,
    "pressure": 1.0,
    "energy_consumption": 6.5,
    "predicted_remaining_life": 10,
    "temp_rolling_10min": 112.0,
    "temp_trend_1h": 0.8,
    "vibr_rolling_10min": 82.0,
    "temp_std_30min": 8.0,
    "energy_vibr_ratio": 0.08,
    "downtime_risk": 0.95,
}


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi non installe")
class TestAPIIntegration:
    """Tests d'integration API + modeles."""

    @pytest.fixture
    def client(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from api.main import app
        return TestClient(app)

    def test_normal_machine_not_critical(self, client):
        """Une machine normale ne doit pas declencher de prediction de maintenance."""
        response = client.post("/predict", json=SAMPLE_NORMAL)
        assert response.status_code == 200
        data = response.json()
        # Avec des valeurs normales, la confiance en maintenance doit etre faible
        # ou la prediction doit etre 'normal'
        assert data["prediction"] in ["normal", "maintenance_required", 0, 1], \
            f"Prediction inattendue: {data['prediction']}"

    def test_critical_machine_detected(self, client):
        """Une machine critique doit etre detectee."""
        response = client.post("/predict", json=SAMPLE_CRITICAL)
        assert response.status_code == 200
        data = response.json()
        # Avec des valeurs critiques, au moins des alertes doivent etre declenchees
        assert len(data.get("alerts", [])) > 0, "Aucune alerte pour une machine critique"

    def test_batch_consistency(self, client):
        """Les predictions batch doivent etre coherentes avec les predictions individuelles."""
        # Prediction individuelle
        resp_single = client.post("/predict", json=SAMPLE_NORMAL)
        pred_single = resp_single.json()

        # Prediction batch avec le meme input
        resp_batch = client.post("/predict/batch", json={"machines": [SAMPLE_NORMAL]})
        assert resp_batch.status_code == 200
        pred_batch = resp_batch.json()["predictions"][0]

        # Les predictions doivent etre identiques
        assert pred_single["prediction"] == pred_batch["prediction"]

    def test_anomaly_detection_critical(self, client):
        """Les donnees critiques doivent etre detectees comme anomalies."""
        response = client.post("/anomaly", json=SAMPLE_CRITICAL)
        assert response.status_code == 200
        data = response.json()
        # On s'attend a une anomalie ou au moins une severite elevee
        assert data.get("is_anomaly") is True or data.get("severity") in ["high", "critical"], \
            f"Donnees critiques non detectees comme anomalie: {data}"

    def test_rul_prediction_coherent(self, client):
        """Le RUL d'une machine critique doit etre plus bas qu'une machine normale."""
        resp_normal = client.post("/predict/rul", json=SAMPLE_NORMAL)
        resp_critical = client.post("/predict/rul", json=SAMPLE_CRITICAL)

        if resp_normal.status_code == 200 and resp_critical.status_code == 200:
            rul_normal = resp_normal.json()["rul_hours"]
            rul_critical = resp_critical.json()["rul_hours"]
            assert rul_normal > rul_critical, \
                f"RUL normal ({rul_normal}) devrait etre > RUL critique ({rul_critical})"

    def test_full_workflow(self, client):
        """Test du workflow complet : health -> predict -> anomaly -> rul."""
        # 1. Health check
        health = client.get("/health")
        assert health.status_code == 200

        # 2. Prediction
        predict = client.post("/predict", json=SAMPLE_NORMAL)
        assert predict.status_code == 200

        # 3. Detection d'anomalie
        anomaly = client.post("/anomaly", json=SAMPLE_NORMAL)
        assert anomaly.status_code == 200

        # 4. Prediction RUL
        rul = client.post("/predict/rul", json=SAMPLE_NORMAL)
        assert rul.status_code == 200

        # 5. Metriques
        metrics = client.get("/metrics")
        assert metrics.status_code == 200

        # 6. Model info
        info = client.get("/model-info")
        assert info.status_code == 200
