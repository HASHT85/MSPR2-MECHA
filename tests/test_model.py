"""
Tests des modeles ML MECHA.
Verifie que les modeles sauvegardes sont chargeables et produisent des predictions coherentes.
"""

import os

import numpy as np
import pytest

try:
    import joblib

    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "saved_models")

FEATURES = [
    "temperature",
    "vibration",
    "humidity",
    "pressure",
    "energy_consumption",
    "temp_rolling_10min",
    "temp_trend_1h",
    "vibr_rolling_10min",
    "temp_std_30min",
    "energy_vibr_ratio",
]


def get_model_path(filename):
    """Trouve le chemin du modele."""
    path = os.path.join(MODEL_DIR, filename)
    return path if os.path.exists(path) else None


def make_sample_input():
    """Cree un echantillon d'entree pour les predictions."""
    return np.array(
        [
            [
                80.0,  # temperature
                45.0,  # vibration
                55.0,  # humidity
                3.0,  # pressure
                3.5,  # energy_consumption
                78.0,  # temp_rolling_10min
                0.02,  # temp_trend_1h
                43.0,  # vibr_rolling_10min
                2.5,  # temp_std_30min
                0.08,  # energy_vibr_ratio
            ]
        ]
    )


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestRandomForest:
    """Tests du modele Random Forest."""

    @pytest.fixture
    def model(self):
        path = get_model_path("random_forest_classifier.joblib")
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
        assert model.n_features_in_ == len(FEATURES), (
            f"Modele attend {model.n_features_in_} features, fourni {len(FEATURES)}"
        )


@pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
class TestXGBoost:
    """Tests du modele XGBoost."""

    @pytest.fixture
    def model(self):
        path = get_model_path("xgboost_classifier.joblib")
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
        # Le RUL regressor utilise les memes 10 features capteurs
        X = make_sample_input()
        pred = model.predict(X)
        assert len(pred) == 1
        assert pred[0] >= 0, "Le RUL predit ne doit pas etre negatif"

    def test_model_predicts_numeric(self, model):
        X = make_sample_input()
        pred = model.predict(X)
        assert isinstance(pred[0], (int, float, np.floating, np.integer))


# ==============================================================================
# Coherence entrainement <-> API (point critique : l'IA doit etre branchee)
# ==============================================================================


class TestModelFilenamesConsistency:
    """Les noms de fichiers sauvegardes par l'entrainement doivent etre
    exactement ceux que l'API charge. Sinon l'API tombe en mode mock."""

    def test_training_and_api_filenames_match(self):
        import importlib.util
        import sys

        root = os.path.join(os.path.dirname(__file__), "..")
        sys.path.insert(0, root)
        from api.main import MODEL_FILES

        spec = importlib.util.spec_from_file_location(
            "train_models",
            os.path.join(root, "models", "training", "train_models.py"),
        )
        train = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(train)

        for key, api_filename in MODEL_FILES.items():
            assert key in train.MODEL_FILENAMES, f"Cle {key} absente de MODEL_FILENAMES"
            expected = f"{train.MODEL_FILENAMES[key]}.joblib"
            assert api_filename == expected, (
                f"Incoherence pour {key} : l'entrainement sauvegarde {expected} "
                f"mais l'API charge {api_filename}"
            )

    @pytest.mark.skipif(not HAS_JOBLIB, reason="joblib non installe")
    def test_api_loads_trained_model_not_mock(self, tmp_path, monkeypatch):
        """Un modele sauvegarde sous le nom d'entrainement doit etre charge par
        l'API et utilise pour /predict (model_used != fallback_heuristic)."""
        from sklearn.ensemble import RandomForestClassifier

        rng = np.random.default_rng(0)
        X = rng.random((40, len(FEATURES)))
        y = np.array([0, 1] * 20)
        clf = RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)
        joblib.dump(clf, tmp_path / "random_forest_classifier.joblib")

        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from fastapi.testclient import TestClient

        import api.main as api_main

        monkeypatch.setattr(api_main, "MODEL_DIR", tmp_path)
        registry = api_main.ModelRegistry()
        registry.load_all()
        assert registry.classifier is not None, registry.load_errors
        monkeypatch.setattr(api_main, "models", registry)

        with TestClient(api_main.app) as client:
            payload = dict(zip(FEATURES, make_sample_input()[0].tolist()))
            response = client.post("/predict", json=payload)
        assert response.status_code == 200
        assert response.json()["model_used"] == "random_forest"
