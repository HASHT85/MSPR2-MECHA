#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MECHA - Script d'entrainement des modeles de maintenance predictive
===================================================================

Projet : MSPR 2, Bloc 4, EPSI RNCP35584
Entreprise : MECHA (fabrication de pieces mecaniques haute precision)
Dataset : ~100k lignes, capteurs IoT (temperature, vibration, humidity, pressure, energy, RUL)

Modeles entraines :
    1. Random Forest Classifier - modele principal (classification maintenance)
    2. XGBoost Classifier - alternative avec scale_pos_weight
    3. Regression Logistique - baseline de reference
    4. Isolation Forest - detection d'anomalies (non supervise)
    5. Random Forest Regressor - prediction RUL (Remaining Useful Life)

REGLES ML APPLIQUEES :
    - machine_status EXCLUE des features (DATA LEAKAGE confirme MSPR 1)
    - Split TEMPOREL 80/20 (trie par timestamp, pas aleatoire)
    - Desequilibre gere : class_weight='balanced', scale_pos_weight
    - Metriques documentees : Accuracy, Precision, Recall, F1, AUC-ROC

Auteur : Equipe MECHA
Date : 2026-05-30
"""

import os
import sys
import json
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
import joblib

# Optionnel : XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[WARN] XGBoost non disponible. Installation : pip install xgboost")

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Chemins
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "mecha_dataset_processed.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "saved_models"
EVAL_DIR = PROJECT_ROOT / "models" / "evaluation"
RESULTS_DIR = EVAL_DIR / "results"

# Features ML (machine_status EXCLUE - DATA LEAKAGE)
FEATURES_CLASSIFICATION = [
    "temperature",
    "vibration",
    "humidity",
    "pressure",
    "energy_consumption",
    "predicted_remaining_life",
    "temp_rolling_10min",
    "temp_trend_1h",
    "vibr_rolling_10min",
    "temp_std_30min",
    "energy_vibr_ratio",
    "downtime_risk",
]

# Variable cible classification
TARGET_CLASSIFICATION = "maintenance_required"

# Variable cible regression (RUL)
TARGET_RUL = "predicted_remaining_life"
FEATURES_RUL = [
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
    "downtime_risk",
]

# Split temporel
TRAIN_RATIO = 0.80

# Random state pour reproductibilite
RANDOM_STATE = 42


def print_separator(char="=", length=70):
    """Affiche une ligne de separation."""
    print(char * length)


def print_header(title):
    """Affiche un en-tete formate."""
    print_separator()
    print(f"  {title}")
    print_separator()


def print_subheader(title):
    """Affiche un sous-en-tete formate."""
    print_separator("-", 50)
    print(f"  {title}")
    print_separator("-", 50)


# =============================================================================
# 1. CHARGEMENT ET PREPARATION DES DONNEES
# =============================================================================

def load_dataset(filepath):
    """
    Charge le dataset MECHA depuis un fichier CSV.

    Args:
        filepath (Path): Chemin vers le fichier CSV.

    Returns:
        pd.DataFrame: DataFrame charge et valide.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si des colonnes requises sont manquantes.
    """
    print_header("1. CHARGEMENT DU DATASET")

    if not filepath.exists():
        raise FileNotFoundError(f"Dataset introuvable : {filepath}")

    df = pd.read_csv(filepath)
    print(f"  [OK] Dataset charge : {filepath.name}")
    print(f"  [OK] Dimensions : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")

    # Verification des colonnes requises
    required_cols = FEATURES_CLASSIFICATION + [TARGET_CLASSIFICATION, "timestamp"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    print(f"  [OK] Toutes les colonnes requises sont presentes")

    # Verification DATA LEAKAGE
    if "machine_status" in FEATURES_CLASSIFICATION:
        raise ValueError(
            "ERREUR CRITIQUE : machine_status dans les features ! "
            "DATA LEAKAGE detecte. Retirer cette variable."
        )
    print(f"  [OK] machine_status EXCLUE des features (anti data leakage)")

    # Distribution de la cible
    target_dist = df[TARGET_CLASSIFICATION].value_counts(normalize=True)
    print(f"\n  Distribution de '{TARGET_CLASSIFICATION}' :")
    for val, pct in target_dist.items():
        label = "POSITIF (maintenance)" if val == 1 else "NEGATIF (pas de maintenance)"
        print(f"    - {label} : {pct*100:.1f}%")

    return df


def prepare_temporal_split(df):
    """
    Prepare un split temporel 80/20 (PAS aleatoire).

    Le split temporel est essentiel pour eviter le data leakage temporel :
    on entraine sur le passe et on teste sur le futur.

    Args:
        df (pd.DataFrame): Dataset complet.

    Returns:
        tuple: (X_train, X_test, y_train, y_test, df_train, df_test)
    """
    print_header("2. SPLIT TEMPOREL 80/20")

    # Conversion timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Tri par timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)
    print(f"  [OK] Donnees triees par timestamp")
    print(f"  [OK] Periode : {df['timestamp'].min()} -> {df['timestamp'].max()}")

    # Split temporel
    split_idx = int(len(df) * TRAIN_RATIO)
    df_train = df.iloc[:split_idx].copy()
    df_test = df.iloc[split_idx:].copy()

    split_date = df_train["timestamp"].max()
    print(f"  [OK] Point de coupure : {split_date}")
    print(f"  [OK] Train : {len(df_train):,} lignes ({len(df_train)/len(df)*100:.1f}%)")
    print(f"  [OK] Test  : {len(df_test):,} lignes ({len(df_test)/len(df)*100:.1f}%)")

    # Preparation X, y pour classification
    X_train = df_train[FEATURES_CLASSIFICATION].copy()
    X_test = df_test[FEATURES_CLASSIFICATION].copy()
    y_train = df_train[TARGET_CLASSIFICATION].copy()
    y_test = df_test[TARGET_CLASSIFICATION].copy()

    # Gestion des valeurs manquantes
    n_missing_train = X_train.isnull().sum().sum()
    n_missing_test = X_test.isnull().sum().sum()
    if n_missing_train > 0 or n_missing_test > 0:
        print(f"  [WARN] Valeurs manquantes detectees : train={n_missing_train}, test={n_missing_test}")
        X_train = X_train.fillna(X_train.median())
        X_test = X_test.fillna(X_train.median())  # Utiliser la mediane du train
        print(f"  [OK] Valeurs manquantes imputees (mediane)")

    # Gestion valeurs infinies
    X_train = X_train.replace([np.inf, -np.inf], np.nan).fillna(X_train.median())
    X_test = X_test.replace([np.inf, -np.inf], np.nan).fillna(X_train.median())

    # Distribution dans train/test
    train_pos_rate = y_train.mean() * 100
    test_pos_rate = y_test.mean() * 100
    print(f"\n  Distribution cible :")
    print(f"    Train : {train_pos_rate:.2f}% positifs")
    print(f"    Test  : {test_pos_rate:.2f}% positifs")

    return X_train, X_test, y_train, y_test, df_train, df_test


# =============================================================================
# 2. ENTRAINEMENT DES MODELES
# =============================================================================

def train_random_forest(X_train, y_train):
    """
    Entraine un Random Forest Classifier avec class_weight='balanced'.

    Le class_weight='balanced' ajuste automatiquement les poids des classes
    inversement proportionnels a leur frequence. Crucial avec un desequilibre
    96.9/3.1.

    Args:
        X_train (pd.DataFrame): Features d'entrainement.
        y_train (pd.Series): Variable cible d'entrainement.

    Returns:
        RandomForestClassifier: Modele entraine.
    """
    print_subheader("Random Forest Classifier")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_features="sqrt",
    )

    start = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - start

    print(f"  [OK] Modele entraine en {elapsed:.2f}s")
    print(f"  [OK] Hyperparametres : n_estimators=200, max_depth=15, class_weight='balanced'")
    print(f"  [OK] Nombre d'arbres : {model.n_estimators}")

    # Feature importances
    importances = pd.Series(model.feature_importances_, index=FEATURES_CLASSIFICATION)
    importances = importances.sort_values(ascending=False)
    print(f"\n  Top 5 features (importance) :")
    for feat, imp in importances.head(5).items():
        bar = "#" * int(imp * 50)
        print(f"    {feat:30s} : {imp:.4f} {bar}")

    return model


def train_xgboost(X_train, y_train):
    """
    Entraine un XGBoost Classifier avec scale_pos_weight.

    scale_pos_weight est calcule comme le ratio negatifs/positifs pour
    compenser le desequilibre des classes.

    Args:
        X_train (pd.DataFrame): Features d'entrainement.
        y_train (pd.Series): Variable cible d'entrainement.

    Returns:
        XGBClassifier: Modele entraine, ou None si XGBoost non disponible.
    """
    print_subheader("XGBoost Classifier")

    if not XGBOOST_AVAILABLE:
        print("  [SKIP] XGBoost non installe. Modele ignore.")
        return None

    # Calcul scale_pos_weight : ratio negatifs / positifs
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    scale_pos_weight = n_neg / n_pos
    print(f"  [OK] scale_pos_weight = {scale_pos_weight:.2f} (negatifs/positifs = {n_neg}/{n_pos})")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        eval_metric="logloss",
        use_label_encoder=False,
        n_jobs=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
    )

    start = time.time()
    model.fit(X_train, y_train, verbose=False)
    elapsed = time.time() - start

    print(f"  [OK] Modele entraine en {elapsed:.2f}s")
    print(f"  [OK] Hyperparametres : n_estimators=200, max_depth=8, lr=0.1")

    # Feature importances
    importances = pd.Series(model.feature_importances_, index=FEATURES_CLASSIFICATION)
    importances = importances.sort_values(ascending=False)
    print(f"\n  Top 5 features (importance) :")
    for feat, imp in importances.head(5).items():
        bar = "#" * int(imp * 50)
        print(f"    {feat:30s} : {imp:.4f} {bar}")

    return model


def train_logistic_regression(X_train, y_train):
    """
    Entraine une Regression Logistique comme baseline.

    Utilise class_weight='balanced' et StandardScaler (la regression logistique
    est sensible a l'echelle des features).

    Args:
        X_train (pd.DataFrame): Features d'entrainement.
        y_train (pd.Series): Variable cible d'entrainement.

    Returns:
        tuple: (LogisticRegression, StandardScaler) - Modele et scaler.
    """
    print_subheader("Regression Logistique (Baseline)")

    # Scaling necessaire pour la regression logistique
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=RANDOM_STATE,
        solver="lbfgs",
        C=1.0,
    )

    start = time.time()
    model.fit(X_train_scaled, y_train)
    elapsed = time.time() - start

    print(f"  [OK] Modele entraine en {elapsed:.2f}s")
    print(f"  [OK] Hyperparametres : C=1.0, class_weight='balanced', solver='lbfgs'")

    # Coefficients
    coefs = pd.Series(np.abs(model.coef_[0]), index=FEATURES_CLASSIFICATION)
    coefs = coefs.sort_values(ascending=False)
    print(f"\n  Top 5 features (|coefficient|) :")
    for feat, coef in coefs.head(5).items():
        bar = "#" * int(coef * 5)
        print(f"    {feat:30s} : {coef:.4f} {bar}")

    return model, scaler


def train_isolation_forest(X_train):
    """
    Entraine un Isolation Forest pour la detection d'anomalies.

    Modele non supervise : n'utilise pas la variable cible.
    contamination est fixe a 0.05 (estimation du taux d'anomalies).

    Args:
        X_train (pd.DataFrame): Features d'entrainement.

    Returns:
        IsolationForest: Modele entraine.
    """
    print_subheader("Isolation Forest (Anomalies)")

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_features=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    start = time.time()
    model.fit(X_train)
    elapsed = time.time() - start

    print(f"  [OK] Modele entraine en {elapsed:.2f}s")
    print(f"  [OK] Hyperparametres : n_estimators=200, contamination=0.05")
    print(f"  [OK] Modele NON supervise (pas de variable cible)")

    return model


def train_rf_regressor_rul(X_train_rul, y_train_rul):
    """
    Entraine un Random Forest Regressor pour la prediction RUL.

    Predit la duree de vie restante (predicted_remaining_life) a partir
    des capteurs IoT.

    Args:
        X_train_rul (pd.DataFrame): Features d'entrainement (sans RUL).
        y_train_rul (pd.Series): Variable cible RUL.

    Returns:
        RandomForestRegressor: Modele entraine.
    """
    print_subheader("Random Forest Regressor (RUL)")

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_features="sqrt",
    )

    start = time.time()
    model.fit(X_train_rul, y_train_rul)
    elapsed = time.time() - start

    print(f"  [OK] Modele entraine en {elapsed:.2f}s")
    print(f"  [OK] Hyperparametres : n_estimators=200, max_depth=15")

    # Feature importances
    importances = pd.Series(model.feature_importances_, index=FEATURES_RUL)
    importances = importances.sort_values(ascending=False)
    print(f"\n  Top 5 features (importance) :")
    for feat, imp in importances.head(5).items():
        bar = "#" * int(imp * 50)
        print(f"    {feat:30s} : {imp:.4f} {bar}")

    return model


# =============================================================================
# 3. EVALUATION DES MODELES
# =============================================================================

def evaluate_classifier(model, X_test, y_test, model_name, scaler=None):
    """
    Evalue un modele de classification et retourne les metriques.

    Args:
        model: Modele entraine.
        X_test (pd.DataFrame): Features de test.
        y_test (pd.Series): Variable cible de test.
        model_name (str): Nom du modele.
        scaler (StandardScaler, optional): Scaler pour les features.

    Returns:
        dict: Dictionnaire des metriques.
    """
    X_eval = X_test.copy()
    if scaler is not None:
        X_eval = scaler.transform(X_eval)

    y_pred = model.predict(X_eval)

    # Probabilites pour AUC-ROC
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_eval)[:, 1]
        auc_roc = roc_auc_score(y_test, y_proba)
    else:
        y_proba = None
        auc_roc = None

    metrics = {
        "model_name": model_name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc_roc": float(auc_roc) if auc_roc is not None else None,
        "n_test_samples": int(len(y_test)),
        "n_positive_test": int(y_test.sum()),
        "n_negative_test": int((y_test == 0).sum()),
    }

    # Matrice de confusion
    cm = confusion_matrix(y_test, y_pred)
    metrics["confusion_matrix"] = {
        "true_negatives": int(cm[0, 0]),
        "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]),
        "true_positives": int(cm[1, 1]),
    }

    return metrics


def evaluate_isolation_forest(model, X_test, y_test):
    """
    Evalue l'Isolation Forest en comparant ses predictions d'anomalies
    avec la variable maintenance_required.

    Note : L'Isolation Forest n'est pas supervise, cette evaluation sert
    a mesurer la correlation entre anomalies detectees et maintenances reelles.

    Args:
        model: IsolationForest entraine.
        X_test (pd.DataFrame): Features de test.
        y_test (pd.Series): Variable cible de test (pour comparaison).

    Returns:
        dict: Dictionnaire des metriques.
    """
    # predictions : 1 = normal, -1 = anomalie
    y_pred_raw = model.predict(X_test)
    # Conversion : -1 -> 1 (anomalie = maintenance potentielle), 1 -> 0 (normal)
    y_pred = (y_pred_raw == -1).astype(int)

    scores = model.decision_function(X_test)

    metrics = {
        "model_name": "Isolation Forest",
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc_roc": float(roc_auc_score(y_test, -scores)),  # scores negatifs = anomalies
        "n_anomalies_detected": int(y_pred.sum()),
        "contamination_effective": float(y_pred.mean()),
        "n_test_samples": int(len(y_test)),
    }

    cm = confusion_matrix(y_test, y_pred)
    metrics["confusion_matrix"] = {
        "true_negatives": int(cm[0, 0]),
        "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]),
        "true_positives": int(cm[1, 1]),
    }

    return metrics


def evaluate_rul_regressor(model, X_test_rul, y_test_rul):
    """
    Evalue le Random Forest Regressor pour la prediction RUL.

    Args:
        model: RandomForestRegressor entraine.
        X_test_rul (pd.DataFrame): Features de test.
        y_test_rul (pd.Series): Variable cible RUL de test.

    Returns:
        dict: Dictionnaire des metriques de regression.
    """
    y_pred = model.predict(X_test_rul)

    metrics = {
        "model_name": "RF Regressor RUL",
        "mae": float(mean_absolute_error(y_test_rul, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test_rul, y_pred))),
        "r2_score": float(r2_score(y_test_rul, y_pred)),
        "mse": float(mean_squared_error(y_test_rul, y_pred)),
        "n_test_samples": int(len(y_test_rul)),
        "y_test_mean": float(y_test_rul.mean()),
        "y_test_std": float(y_test_rul.std()),
        "y_pred_mean": float(np.mean(y_pred)),
        "y_pred_std": float(np.std(y_pred)),
    }

    return metrics


def print_classification_results(metrics):
    """Affiche les resultats d'un modele de classification en ASCII pur."""
    name = metrics["model_name"]
    print(f"\n  [{name}]")
    print(f"    Accuracy  : {metrics['accuracy']:.4f}  ({metrics['accuracy']*100:.2f}%)")
    print(f"    Precision : {metrics['precision']:.4f}  ({metrics['precision']*100:.2f}%)")
    print(f"    Recall    : {metrics['recall']:.4f}  ({metrics['recall']*100:.2f}%)")
    print(f"    F1-Score  : {metrics['f1_score']:.4f}  ({metrics['f1_score']*100:.2f}%)")
    if metrics.get("auc_roc") is not None:
        print(f"    AUC-ROC   : {metrics['auc_roc']:.4f}  ({metrics['auc_roc']*100:.2f}%)")
    else:
        print(f"    AUC-ROC   : N/A")

    if "confusion_matrix" in metrics:
        cm = metrics["confusion_matrix"]
        print(f"\n    Matrice de confusion :")
        print(f"                   Pred=0    Pred=1")
        print(f"      Reel=0      {cm['true_negatives']:>7}   {cm['false_positives']:>7}")
        print(f"      Reel=1      {cm['false_negatives']:>7}   {cm['true_positives']:>7}")


def print_rul_results(metrics):
    """Affiche les resultats du modele RUL en ASCII pur."""
    name = metrics["model_name"]
    print(f"\n  [{name}]")
    print(f"    MAE       : {metrics['mae']:.4f}")
    print(f"    RMSE      : {metrics['rmse']:.4f}")
    print(f"    R2 Score  : {metrics['r2_score']:.4f}  ({metrics['r2_score']*100:.2f}%)")
    print(f"    MSE       : {metrics['mse']:.4f}")
    print(f"    Y_test    : mean={metrics['y_test_mean']:.2f}, std={metrics['y_test_std']:.2f}")
    print(f"    Y_pred    : mean={metrics['y_pred_mean']:.2f}, std={metrics['y_pred_std']:.2f}")


# =============================================================================
# 4. SAUVEGARDE DES MODELES ET RESULTATS
# =============================================================================

def save_model(model, model_name, directory, scaler=None):
    """
    Sauvegarde un modele entraine au format joblib.

    Args:
        model: Modele entraine.
        model_name (str): Nom du fichier (sans extension).
        directory (Path): Repertoire de sauvegarde.
        scaler (StandardScaler, optional): Scaler a sauvegarder.
    """
    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / f"{model_name}.joblib"
    joblib.dump(model, filepath)
    print(f"  [OK] Modele sauvegarde : {filepath.name}")

    if scaler is not None:
        scaler_path = directory / f"{model_name}_scaler.joblib"
        joblib.dump(scaler, scaler_path)
        print(f"  [OK] Scaler sauvegarde : {scaler_path.name}")


def save_metrics(all_metrics, directory):
    """
    Sauvegarde toutes les metriques en JSON.

    Args:
        all_metrics (dict): Dictionnaire de toutes les metriques.
        directory (Path): Repertoire de sauvegarde.
    """
    directory.mkdir(parents=True, exist_ok=True)

    # Sauvegarde globale
    filepath = directory / "all_models_metrics.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False, default=str)
    print(f"  [OK] Metriques globales : {filepath.name}")

    # Sauvegarde individuelle par modele
    for model_key, metrics in all_metrics.get("models", {}).items():
        filepath = directory / f"{model_key}_metrics.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
        print(f"  [OK] Metriques {model_key} : {filepath.name}")


def print_comparison_table(all_classifier_metrics):
    """Affiche un tableau comparatif des modeles de classification en ASCII pur."""
    print_header("TABLEAU COMPARATIF DES MODELES")

    header = f"{'Modele':<25} {'Acc':>8} {'Prec':>8} {'Recall':>8} {'F1':>8} {'AUC-ROC':>8}"
    print(header)
    print("-" * len(header))

    for metrics in all_classifier_metrics:
        auc = f"{metrics['auc_roc']:.4f}" if metrics.get('auc_roc') is not None else "N/A"
        print(
            f"{metrics['model_name']:<25} "
            f"{metrics['accuracy']:>8.4f} "
            f"{metrics['precision']:>8.4f} "
            f"{metrics['recall']:>8.4f} "
            f"{metrics['f1_score']:>8.4f} "
            f"{auc:>8}"
        )

    # Meilleur modele par F1-Score
    best = max(all_classifier_metrics, key=lambda m: m["f1_score"])
    print(f"\n  >> Meilleur modele (F1-Score) : {best['model_name']} ({best['f1_score']:.4f})")


# =============================================================================
# 5. PIPELINE PRINCIPAL
# =============================================================================

def main():
    """
    Pipeline principal d'entrainement et d'evaluation.

    Etapes :
        1. Charger le dataset
        2. Preparer le split temporel
        3. Entrainer les 5 modeles
        4. Evaluer chaque modele
        5. Sauvegarder modeles et metriques
        6. Afficher le tableau comparatif
    """
    total_start = time.time()

    print("\n")
    print_separator("*", 70)
    print("  MECHA - Entrainement des modeles de maintenance predictive")
    print(f"  Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator("*", 70)

    # -----------------------------------------------------------------
    # Etape 1 : Chargement
    # -----------------------------------------------------------------
    df = load_dataset(DATA_PATH)

    # -----------------------------------------------------------------
    # Etape 2 : Split temporel
    # -----------------------------------------------------------------
    X_train, X_test, y_train, y_test, df_train, df_test = prepare_temporal_split(df)

    # Preparation donnees RUL
    X_train_rul = df_train[FEATURES_RUL].copy()
    X_test_rul = df_test[FEATURES_RUL].copy()
    y_train_rul = df_train[TARGET_RUL].copy()
    y_test_rul = df_test[TARGET_RUL].copy()

    # Gestion valeurs manquantes/infinies pour RUL
    X_train_rul = X_train_rul.replace([np.inf, -np.inf], np.nan).fillna(X_train_rul.median())
    X_test_rul = X_test_rul.replace([np.inf, -np.inf], np.nan).fillna(X_train_rul.median())

    # -----------------------------------------------------------------
    # Etape 3 : Entrainement
    # -----------------------------------------------------------------
    print_header("3. ENTRAINEMENT DES MODELES")

    # 3.1 Random Forest
    rf_model = train_random_forest(X_train, y_train)

    # 3.2 XGBoost
    xgb_model = train_xgboost(X_train, y_train)

    # 3.3 Regression Logistique
    lr_model, lr_scaler = train_logistic_regression(X_train, y_train)

    # 3.4 Isolation Forest
    iso_model = train_isolation_forest(X_train)

    # 3.5 RF Regressor RUL
    rul_model = train_rf_regressor_rul(X_train_rul, y_train_rul)

    # -----------------------------------------------------------------
    # Etape 4 : Evaluation
    # -----------------------------------------------------------------
    print_header("4. EVALUATION DES MODELES")

    all_classifier_metrics = []

    # Eval Random Forest
    rf_metrics = evaluate_classifier(rf_model, X_test, y_test, "Random Forest")
    print_classification_results(rf_metrics)
    all_classifier_metrics.append(rf_metrics)

    # Eval XGBoost
    if xgb_model is not None:
        xgb_metrics = evaluate_classifier(xgb_model, X_test, y_test, "XGBoost")
        print_classification_results(xgb_metrics)
        all_classifier_metrics.append(xgb_metrics)

    # Eval Regression Logistique
    lr_metrics = evaluate_classifier(lr_model, X_test, y_test, "Logistic Regression", scaler=lr_scaler)
    print_classification_results(lr_metrics)
    all_classifier_metrics.append(lr_metrics)

    # Eval Isolation Forest
    iso_metrics = evaluate_isolation_forest(iso_model, X_test, y_test)
    print_classification_results(iso_metrics)
    all_classifier_metrics.append(iso_metrics)

    # Eval RUL Regressor
    rul_metrics = evaluate_rul_regressor(rul_model, X_test_rul, y_test_rul)
    print_rul_results(rul_metrics)

    # -----------------------------------------------------------------
    # Etape 5 : Tableau comparatif
    # -----------------------------------------------------------------
    print_comparison_table(all_classifier_metrics)

    # -----------------------------------------------------------------
    # Etape 6 : Sauvegarde
    # -----------------------------------------------------------------
    print_header("5. SAUVEGARDE DES MODELES ET METRIQUES")

    # Sauvegarder les modeles
    save_model(rf_model, "random_forest_classifier", MODELS_DIR)
    if xgb_model is not None:
        save_model(xgb_model, "xgboost_classifier", MODELS_DIR)
    save_model(lr_model, "logistic_regression", MODELS_DIR, scaler=lr_scaler)
    save_model(iso_model, "isolation_forest", MODELS_DIR)
    save_model(rul_model, "rf_regressor_rul", MODELS_DIR)

    # Preparer toutes les metriques
    all_metrics = {
        "metadata": {
            "project": "MECHA - Maintenance Predictive",
            "date": datetime.now().isoformat(),
            "dataset": str(DATA_PATH.name),
            "n_total_samples": int(len(df)),
            "n_train_samples": int(len(X_train)),
            "n_test_samples": int(len(X_test)),
            "split_method": "temporal_80_20",
            "features_used": FEATURES_CLASSIFICATION,
            "target_variable": TARGET_CLASSIFICATION,
            "data_leakage_exclusions": ["machine_status"],
            "imbalance_handling": "class_weight_balanced / scale_pos_weight",
        },
        "models": {
            "random_forest": rf_metrics,
            "logistic_regression": lr_metrics,
            "isolation_forest": iso_metrics,
            "rf_regressor_rul": rul_metrics,
        },
    }

    if xgb_model is not None:
        all_metrics["models"]["xgboost"] = xgb_metrics

    # Sauvegarder les metriques
    save_metrics(all_metrics, RESULTS_DIR)

    # -----------------------------------------------------------------
    # Resume final
    # -----------------------------------------------------------------
    total_elapsed = time.time() - total_start

    print_header("RESUME FINAL")
    print(f"  Temps total d'execution : {total_elapsed:.2f}s")
    print(f"  Modeles sauvegardes dans : {MODELS_DIR}")
    print(f"  Metriques sauvegardees dans : {RESULTS_DIR}")
    print(f"  Nombre de modeles entraines : {4 + (1 if xgb_model else 0)}")
    print(f"\n  Features utilisees ({len(FEATURES_CLASSIFICATION)}) :")
    for feat in FEATURES_CLASSIFICATION:
        print(f"    - {feat}")
    print(f"\n  [OK] Pipeline termine avec succes !")
    print_separator("*", 70)


if __name__ == "__main__":
    main()
