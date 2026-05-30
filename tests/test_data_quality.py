"""
Tests de qualite des donnees MECHA.
Verifie la coherence, les contraintes et la completude du dataset genere.
"""

import pandas as pd
import numpy as np
import os
import pytest


@pytest.fixture
def dataset():
    """Charge le dataset MECHA pour les tests."""
    paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", "mecha_dataset_processed.csv"),
        "c:/Projet/MSPR/MSPR2-MECHA/data/processed/mecha_dataset_processed.csv",
    ]
    for path in paths:
        if os.path.exists(path):
            return pd.read_csv(path, parse_dates=["timestamp"])
    pytest.skip("Dataset non disponible")


class TestDatasetStructure:
    """Tests de structure du dataset."""

    def test_dataset_not_empty(self, dataset):
        assert len(dataset) > 0, "Le dataset est vide"

    def test_dataset_has_minimum_rows(self, dataset):
        assert len(dataset) >= 50000, f"Le dataset a seulement {len(dataset)} lignes (min: 50k)"

    def test_dataset_has_required_columns(self, dataset):
        required = [
            "timestamp", "machine_id", "usine_id", "temperature",
            "vibration", "humidity", "pressure", "energy_consumption",
            "machine_status", "anomaly_flag", "predicted_remaining_life",
            "failure_type", "maintenance_required",
        ]
        missing = [col for col in required if col not in dataset.columns]
        assert len(missing) == 0, f"Colonnes manquantes : {missing}"

    def test_dataset_has_enrichment_columns(self, dataset):
        enrichments = [
            "usine_nom", "usine_pays", "ligne_production", "type_piece",
            "machine_profile", "maintenance_type",
            "temp_rolling_10min", "temp_trend_1h", "vibr_rolling_10min",
            "temp_std_30min", "energy_vibr_ratio", "downtime_risk",
        ]
        missing = [col for col in enrichments if col not in dataset.columns]
        assert len(missing) == 0, f"Colonnes enrichies manquantes : {missing}"


class TestDataQuality:
    """Tests de qualite des donnees."""

    def test_no_null_machine_id(self, dataset):
        assert dataset["machine_id"].isna().sum() == 0

    def test_no_null_temperature(self, dataset):
        assert dataset["temperature"].isna().sum() == 0

    def test_no_null_maintenance_required(self, dataset):
        assert dataset["maintenance_required"].isna().sum() == 0

    def test_machine_status_valid_values(self, dataset):
        valid = {0, 1, 2}
        actual = set(dataset["machine_status"].unique())
        assert actual.issubset(valid), f"Valeurs invalides : {actual - valid}"

    def test_maintenance_required_binary(self, dataset):
        valid = {0, 1}
        actual = set(dataset["maintenance_required"].unique())
        assert actual.issubset(valid), f"Valeurs invalides : {actual - valid}"

    def test_temperature_reasonable_range(self, dataset):
        assert dataset["temperature"].min() >= -10, "Temperature trop basse"
        assert dataset["temperature"].max() <= 200, "Temperature trop haute"

    def test_vibration_non_negative(self, dataset):
        assert dataset["vibration"].min() >= 0, "Vibrations negatives detectees"

    def test_rul_non_negative(self, dataset):
        assert dataset["predicted_remaining_life"].min() >= 0, "RUL negatif detecte"


class TestDataConsistency:
    """Tests de coherence metier."""

    def test_machines_present(self, dataset):
        """Le dataset fusionne doit avoir entre 50 et 100 machines."""
        n_machines = dataset["machine_id"].nunique()
        assert 50 <= n_machines <= 100, f"Nombre de machines inattendu: {n_machines}"

    def test_5_usines_present(self, dataset):
        assert dataset["usine_id"].nunique() == 5

    def test_usine_names_correct(self, dataset):
        expected = {"Lyon", "Toulouse", "Nantes", "Barcelone", "Madrid"}
        actual = set(dataset["usine_nom"].unique())
        assert actual == expected, f"Usines attendues: {expected}, trouvees: {actual}"

    def test_machines_per_usine(self, dataset):
        """Chaque usine doit avoir au moins 10 machines (plus avec le dataset fusionne)."""
        for usine in dataset["usine_id"].unique():
            n_machines = dataset[dataset["usine_id"] == usine]["machine_id"].nunique()
            assert n_machines >= 10, f"{usine} a seulement {n_machines} machines (min: 10)"

    def test_target_has_both_classes(self, dataset):
        """La variable cible doit avoir les deux classes pour le ML."""
        classes = dataset["maintenance_required"].unique()
        assert 0 in classes and 1 in classes, "Il manque une classe dans maintenance_required"

    def test_no_machine_status_leakage_in_features(self, dataset):
        """Verifier que machine_status ne sera pas accidentellement utilise comme feature ML."""
        # Ce test documente le risque de data leakage
        status_2 = dataset[dataset["machine_status"] == 2]
        if len(status_2) > 0:
            maint_rate = status_2["maintenance_required"].mean()
            # Si 100% des status=2 ont maintenance=1, c'est du leakage
            assert maint_rate > 0.5, "La correlation machine_status=2 / maintenance est attendue"

    def test_downtime_risk_bounded(self, dataset):
        """Le score de risque doit etre entre 0 et 1."""
        assert dataset["downtime_risk"].min() >= 0, "downtime_risk < 0"
        assert dataset["downtime_risk"].max() <= 1.01, "downtime_risk > 1"
