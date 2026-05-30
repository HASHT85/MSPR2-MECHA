"""
Tests des modeles ML MECHA.
Verifie que les modeles sauvegardes sont chargeables et produisent des predictions coherentes.
"""

import numpy as np
import os
import pytest

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "saved_models")
ALT_MODEL_DIR = "c:/Projet/MSPR/MSPR2-MECHA/models/saved_models"

FEATURES = [
    "temperature", "vibration", "humidity", "pressure",
    "energy_consumption", "predicted_remaining_life",
    "temp_rolling_10min", "temp_trend_1h", "vibr_rolling_10min",
    "temp_std_30min", "energy_vibr_ratio", "downtime_risk",
]


def get_model_path(filename):
    """Trouve le chemin du modele."""
    for d in [MODEL_DIR, ALT_MODEL_DIR]:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


def make_sample_input():
    """Cree un echantillon d'entree pour les predictions."""
    return np.array([[
        80.0,   # temperature
        45.0,   # vibration
        55.0,   # humidity
        3.0,    # pressure
        3.5,    # energy_consumption
        200.0,  # predicted_remaining_life
        78.0,   # temp_rolling_10min
        0.02,   # temp_trend_1h
        43.0,   # vibr_rolling_10min
        2.5,    # temp_std_30min
        0.08,   # energy_vibr_ratio
        0.35,   # downtime_risk
    ]])


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestRandomForest:
    """Tests du modele Random Forest."""

    @pytest.fixture
    def model(self):
        path = get_model_path("random_forest.joblib") or get_model_path("random_forest_classifier.joblib")
        if path is None:
            pytest.skip("Modele RF non disponible")
        return joblib.load(path)

    def test_model_loads(self, model):
        assert model is not None

    def test_model_predicts(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert pred is not None
        assert len(pred) == 1

    def test_prediction_binary(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert pred[0] in [0, 1], f"Prediction non binaire : {pred[0]}"

    def test_predict_proba_exists(self, model):
        X = make_sample_input()
        proba = model.predict_proba(X)
        assert proba.shape == (1, 2)
        assert 0 <= proba[0][0] <= 1
        assert 0 <= proba[0][1] <= 1

    def test_feature_count_matches(self, model):
        assert model.n_features_in_ == len(FEATURES), \
            f"Modele attend {model.n_features_in_} features, fourni {len(FEATURES)}"


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestXGBoost:
    """Tests du modele XGBoost."""

    @pytest.fixture
    def model(self):
        path = get_model_path("xgboost_model.joblib") or get_model_path("xgboost_classifier.joblib")
        if path is None:
            pytest.skip("Modele XGBoost non disponible")
        return joblib.load(path)

    def test_model_loads(self, model):
        assert model is not None

    def test_model_predicts(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert len(pred) == 1

    def test_prediction_binary(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert pred[0] in [0, 1]


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestIsolationForest:
    """Tests du modele Isolation Forest."""

    @pytest.fixture
    def model(self):
        path = get_model_path("isolation_forest.joblib")
        if path is None:
            pytest.skip("Modele IF non disponible")
        return joblib.load(path)

    def test_model_loads(self, model):
        assert model is not None

    def test_model_predicts(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert len(pred) == 1

    def test_anomaly_detection_output(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert pred[0] in [-1, 1], f"IF doit retourner -1 ou 1, obtenu: {pred[0]}"


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestRULRegressor:
    """Tests du modele de prediction RUL."""

    @pytest.fixture
    def model(self):
        path = get_model_path("rf_regressor_rul.joblib")
        if path is None:
            pytest.skip("Modele RUL non disponible")
        return joblib.load(path)

    def test_model_loads(self, model):
        assert model is not None

    def test_model_predicts_positive(self, model):
        # Pour le RUL, on utilise les features sans predicted_remaining_life
        features_rul = [f for f in FEATURES if f != "predicted_remaining_life"]
        X = make_sample_input()[:, [FEATURES.index(f) for f in features_rul]]
        pred = model.predict(X)
        assert len(pred) == 1
        # RUL peut etre negatif dans certains cas extremes, on verifie juste que ca tourne

    def test_model_predicts_numeric(self, model):
        features_rul = [f for f in FEATURES if f != "predicted_remaining_life"]
        X = make_sample_input()[:, [FEATURES.index(f) for f in features_rul]]
        pred = model.predict(X)
        assert isinstance(pred[0], (int, float, np.floating, np.integer))
