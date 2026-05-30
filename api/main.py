"""
MSPR 2 MECHA -- API FastAPI de maintenance predictive industrielle.

Cette API expose les modeles de Machine Learning entraines pour :
- La classification de l'etat de maintenance des machines
- L'estimation du temps restant avant defaillance (RUL)
- La detection d'anomalies via Isolation Forest
- La gestion des seuils d'alerte configurables

Auteurs : Equipe MECHA (EPSI RNCP35584)
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# ==============================================================================
# Configuration
# ==============================================================================

# Chemin des modeles (relatif a la racine du projet ou absolu)
MODEL_DIR = Path(os.getenv("MODEL_PATH", "models/saved_models"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
API_VERSION = "1.0.0"
API_TITLE = "MECHA -- API Maintenance Predictive"
API_DESCRIPTION = (
    "API REST pour la maintenance predictive industrielle MECHA. "
    "Expose les modeles IA (Random Forest, XGBoost, Isolation Forest) "
    "pour la prediction de pannes, l'estimation RUL et la detection d'anomalies."
)

# Configuration du logging structure
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("mecha.api")


# ==============================================================================
# Features ML attendues par les modeles
# ==============================================================================

ML_FEATURE_NAMES: list[str] = [
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


# ==============================================================================
# Chargement des modeles ML
# ==============================================================================

class ModelRegistry:
    """Registre central des modeles ML charges en memoire."""

    def __init__(self) -> None:
        self.classifier: Any = None          # Random Forest (classification)
        self.xgboost: Any = None             # XGBoost (classification)
        self.isolation_forest: Any = None    # Isolation Forest (anomalies)
        self.rul_regressor: Any = None       # RF Regressor (RUL)
        self.loaded: bool = False
        self.load_errors: dict[str, str] = {}
        self.load_timestamp: Optional[str] = None

    def load_all(self) -> None:
        """Charge tous les modeles depuis le disque. Fallback gracieux si absent."""
        try:
            import joblib
        except ImportError:
            logger.warning("joblib non disponible -- les modeles ne seront pas charges")
            self.load_errors["joblib"] = "Module joblib non installe"
            return

        model_files = {
            "classifier": "random_forest.joblib",
            "xgboost": "xgboost_model.joblib",
            "isolation_forest": "isolation_forest.joblib",
            "rul_regressor": "rf_regressor_rul.joblib",
        }

        any_loaded = False
        for attr, filename in model_files.items():
            filepath = MODEL_DIR / filename
            try:
                if filepath.exists():
                    model = joblib.load(filepath)
                    setattr(self, attr, model)
                    logger.info("Modele charge : %s depuis %s", attr, filepath)
                    any_loaded = True
                else:
                    msg = f"Fichier introuvable : {filepath}"
                    logger.warning(msg)
                    self.load_errors[attr] = msg
            except Exception as exc:
                msg = f"Erreur chargement {filename} : {exc}"
                logger.error(msg)
                self.load_errors[attr] = msg

        self.loaded = any_loaded
        self.load_timestamp = datetime.now(timezone.utc).isoformat()

        if not any_loaded:
            logger.warning(
                "Aucun modele charge -- l'API fonctionnera en mode fallback/mock"
            )


# Instance globale du registre
models = ModelRegistry()


# ==============================================================================
# Seuils d'alerte MECHA (configuration mutable)
# ==============================================================================

class AlertThresholds:
    """Seuils d'alerte configurables pour le systeme MECHA."""

    def __init__(self) -> None:
        self.reset_defaults()

    def reset_defaults(self) -> None:
        """Reinitialise les seuils aux valeurs par defaut MECHA."""
        self.temperature_critical: float = float(
            os.getenv("ALERT_TEMP_CRITICAL", "100")
        )
        self.rebuts_max_percent: float = float(
            os.getenv("ALERT_REBUTS_MAX", "3.0")
        )
        self.trs_min_percent: float = float(
            os.getenv("ALERT_TRS_MIN", "75")
        )
        self.cycle_deviation_max_percent: float = float(
            os.getenv("ALERT_CYCLE_DEVIATION", "15")
        )
        self.anomaly_rate_max_percent: float = float(
            os.getenv("ALERT_ANOMALY_MAX", "10")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature_critical_celsius": self.temperature_critical,
            "rebuts_max_percent": self.rebuts_max_percent,
            "trs_min_percent": self.trs_min_percent,
            "cycle_deviation_max_percent": self.cycle_deviation_max_percent,
            "anomaly_rate_max_percent": self.anomaly_rate_max_percent,
        }


alert_thresholds = AlertThresholds()


# ==============================================================================
# Modeles Pydantic -- Schemas d'entree / sortie
# ==============================================================================

class SensorInput(BaseModel):
    """Donnees capteur d'une machine pour la prediction."""

    temperature: float = Field(
        ..., ge=-50, le=500, description="Temperature en degres Celsius"
    )
    vibration: float = Field(
        ..., ge=0, le=100, description="Niveau de vibration (mm/s)"
    )
    humidity: float = Field(
        ..., ge=0, le=100, description="Humidite relative (%)"
    )
    pressure: float = Field(
        ..., ge=0, le=2000, description="Pression (hPa)"
    )
    energy_consumption: float = Field(
        ..., ge=0, description="Consommation energetique (kWh)"
    )
    predicted_remaining_life: float = Field(
        ..., ge=0, description="Duree de vie restante estimee (heures)"
    )
    temp_rolling_10min: Optional[float] = Field(
        None, description="Moyenne glissante temperature 10 min"
    )
    temp_trend_1h: Optional[float] = Field(
        None, description="Tendance temperature sur 1h"
    )
    vibr_rolling_10min: Optional[float] = Field(
        None, description="Moyenne glissante vibration 10 min"
    )
    temp_std_30min: Optional[float] = Field(
        None, description="Ecart-type temperature 30 min"
    )
    energy_vibr_ratio: Optional[float] = Field(
        None, description="Ratio energie / vibration"
    )
    downtime_risk: Optional[float] = Field(
        None, ge=0, le=1, description="Risque d'arret (0-1)"
    )
    machine_id: Optional[str] = Field(
        None, description="Identifiant de la machine"
    )

    model_config = {"json_schema_extra": {
        "examples": [{
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
        }]
    }}


class PredictionResponse(BaseModel):
    """Reponse de prediction de maintenance."""

    machine_id: Optional[str] = None
    prediction: str = Field(
        ..., description="Etat predit : 'normal' ou 'maintenance_required'"
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Score de confiance (0-1)"
    )
    risk_level: str = Field(
        ..., description="Niveau de risque : 'low', 'medium', 'high', 'critical'"
    )
    alerts: list[str] = Field(
        default_factory=list, description="Alertes declenchees"
    )
    model_used: str = Field(
        ..., description="Modele utilise pour la prediction"
    )
    timestamp: str = Field(
        ..., description="Horodatage de la prediction (ISO 8601)"
    )


class BatchInput(BaseModel):
    """Entree pour les predictions en batch."""

    machines: list[SensorInput] = Field(
        ..., min_length=1, max_length=100,
        description="Liste des machines (max 100)"
    )


class BatchResponse(BaseModel):
    """Reponse pour les predictions en batch."""

    predictions: list[PredictionResponse]
    total: int
    processing_time_ms: float


class RULInput(BaseModel):
    """Entree pour la prediction RUL (Remaining Useful Life)."""

    temperature: float = Field(..., ge=-50, le=500)
    vibration: float = Field(..., ge=0, le=100)
    humidity: float = Field(..., ge=0, le=100)
    pressure: float = Field(..., ge=0, le=2000)
    energy_consumption: float = Field(..., ge=0)
    predicted_remaining_life: float = Field(..., ge=0)
    temp_rolling_10min: Optional[float] = None
    temp_trend_1h: Optional[float] = None
    vibr_rolling_10min: Optional[float] = None
    temp_std_30min: Optional[float] = None
    energy_vibr_ratio: Optional[float] = None
    downtime_risk: Optional[float] = None
    machine_id: Optional[str] = None


class RULResponse(BaseModel):
    """Reponse de prediction RUL."""

    machine_id: Optional[str] = None
    rul_hours: float = Field(
        ..., description="Temps restant estime avant panne (heures)"
    )
    rul_category: str = Field(
        ..., description="Categorie : 'urgent', 'soon', 'moderate', 'safe'"
    )
    confidence: float = Field(..., ge=0, le=1)
    model_used: str
    timestamp: str


class AnomalyInput(BaseModel):
    """Entree pour la detection d'anomalies."""

    temperature: float = Field(..., ge=-50, le=500)
    vibration: float = Field(..., ge=0, le=100)
    humidity: float = Field(..., ge=0, le=100)
    pressure: float = Field(..., ge=0, le=2000)
    energy_consumption: float = Field(..., ge=0)
    predicted_remaining_life: float = Field(..., ge=0)
    temp_rolling_10min: Optional[float] = None
    temp_trend_1h: Optional[float] = None
    vibr_rolling_10min: Optional[float] = None
    temp_std_30min: Optional[float] = None
    energy_vibr_ratio: Optional[float] = None
    downtime_risk: Optional[float] = None
    machine_id: Optional[str] = None


class AnomalyResponse(BaseModel):
    """Reponse de detection d'anomalie."""

    machine_id: Optional[str] = None
    is_anomaly: bool = Field(..., description="True si anomalie detectee")
    anomaly_score: float = Field(
        ..., description="Score d'anomalie (plus negatif = plus anormal)"
    )
    severity: str = Field(
        ..., description="Severite : 'normal', 'warning', 'critical'"
    )
    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Facteurs contributifs a l'anomalie"
    )
    model_used: str
    timestamp: str


class AlertConfigInput(BaseModel):
    """Schema de mise a jour des seuils d'alerte."""

    temperature_critical_celsius: Optional[float] = Field(
        None, gt=0, le=1000,
        description="Seuil critique temperature (Celsius)"
    )
    rebuts_max_percent: Optional[float] = Field(
        None, gt=0, le=100,
        description="Taux de rebuts max (%)"
    )
    trs_min_percent: Optional[float] = Field(
        None, ge=0, le=100,
        description="TRS minimum acceptable (%)"
    )
    cycle_deviation_max_percent: Optional[float] = Field(
        None, gt=0, le=100,
        description="Deviation cycle max (%)"
    )
    anomaly_rate_max_percent: Optional[float] = Field(
        None, gt=0, le=100,
        description="Taux d'anomalie max (%)"
    )


class AlertConfigResponse(BaseModel):
    """Schema de reponse des seuils d'alerte."""

    temperature_critical_celsius: float
    rebuts_max_percent: float
    trs_min_percent: float
    cycle_deviation_max_percent: float
    anomaly_rate_max_percent: float
    updated_at: str


class HealthResponse(BaseModel):
    """Reponse du health check."""

    status: str
    version: str
    models_loaded: bool
    models_available: dict[str, bool]
    uptime_seconds: float
    timestamp: str


class ModelInfoResponse(BaseModel):
    """Informations sur les modeles (model card resumee)."""

    project: str
    version: str
    models: list[dict[str, Any]]
    features: list[str]
    alert_thresholds: dict[str, Any]
    compliance: dict[str, str]


class MetricsResponse(BaseModel):
    """Metriques de performance du modele."""

    models: dict[str, Any]
    api_stats: dict[str, Any]
    timestamp: str


# ==============================================================================
# Compteurs API (metriques simples en memoire)
# ==============================================================================

class APIStats:
    """Compteurs de requetes pour les metriques."""

    def __init__(self) -> None:
        self.total_predictions: int = 0
        self.total_anomaly_checks: int = 0
        self.total_rul_predictions: int = 0
        self.total_batch_predictions: int = 0
        self.total_errors: int = 0
        self.start_time: float = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_predictions": self.total_predictions,
            "total_anomaly_checks": self.total_anomaly_checks,
            "total_rul_predictions": self.total_rul_predictions,
            "total_batch_predictions": self.total_batch_predictions,
            "total_errors": self.total_errors,
            "uptime_seconds": round(time.time() - self.start_time, 2),
        }


api_stats = APIStats()


# ==============================================================================
# Helpers -- logique de prediction
# ==============================================================================

def _extract_features(data: SensorInput | RULInput | AnomalyInput) -> np.ndarray:
    """Extrait le vecteur de features depuis un schema Pydantic."""
    values = []
    for feat in ML_FEATURE_NAMES:
        val = getattr(data, feat, None)
        if val is None:
            # Fallback : calculer les features derivees si possible
            if feat == "temp_rolling_10min":
                val = getattr(data, "temperature", 0.0)
            elif feat == "temp_trend_1h":
                val = 0.0
            elif feat == "vibr_rolling_10min":
                val = getattr(data, "vibration", 0.0)
            elif feat == "temp_std_30min":
                val = 1.0
            elif feat == "energy_vibr_ratio":
                vibr = getattr(data, "vibration", 1.0)
                energy = getattr(data, "energy_consumption", 0.0)
                val = energy / vibr if vibr > 0 else 0.0
            elif feat == "downtime_risk":
                val = 0.5
            else:
                val = 0.0
        values.append(float(val))
    return np.array(values).reshape(1, -1)


def _evaluate_alerts(data: SensorInput | RULInput | AnomalyInput) -> list[str]:
    """Evalue les seuils d'alerte MECHA et retourne les alertes declenchees."""
    alerts: list[str] = []
    temp = getattr(data, "temperature", 0.0)
    if temp > alert_thresholds.temperature_critical:
        alerts.append(
            f"CRITIQUE : Temperature {temp} C depasse le seuil "
            f"de {alert_thresholds.temperature_critical} C"
        )
    return alerts


def _risk_level_from_confidence(confidence: float, prediction: int) -> str:
    """Determine le niveau de risque a partir de la prediction et de la confiance."""
    if prediction == 0:
        # Prediction normale
        if confidence > 0.8:
            return "low"
        return "medium"
    # Prediction de maintenance requise
    if confidence > 0.8:
        return "critical"
    if confidence > 0.6:
        return "high"
    return "medium"


def _rul_category(rul_hours: float) -> str:
    """Classifie le RUL en categorie humaine."""
    if rul_hours < 24:
        return "urgent"
    if rul_hours < 72:
        return "soon"
    if rul_hours < 168:
        return "moderate"
    return "safe"


def _mock_predict(features: np.ndarray) -> tuple[int, float]:
    """Prediction mock quand aucun modele n'est charge.

    Utilise des heuristiques simples basees sur les seuils MECHA.
    """
    temp = features[0, 0]
    vibration = features[0, 1]
    energy = features[0, 4]

    # Score de risque heuristique
    risk_score = 0.0
    if temp > alert_thresholds.temperature_critical:
        risk_score += 0.4
    elif temp > alert_thresholds.temperature_critical * 0.8:
        risk_score += 0.2
    if vibration > 5.0:
        risk_score += 0.3
    elif vibration > 3.0:
        risk_score += 0.1
    if energy > 200:
        risk_score += 0.2

    risk_score = min(risk_score, 1.0)
    prediction = 1 if risk_score > 0.5 else 0
    confidence = max(risk_score, 1.0 - risk_score)
    return prediction, round(confidence, 4)


def _mock_rul(features: np.ndarray) -> float:
    """Estimation RUL mock basee sur des heuristiques."""
    temp = features[0, 0]
    vibration = features[0, 1]
    remaining = features[0, 5]

    # Plus la temperature et les vibrations sont elevees, moins il reste de temps
    base_rul = remaining
    if temp > alert_thresholds.temperature_critical:
        base_rul *= 0.3
    elif temp > alert_thresholds.temperature_critical * 0.8:
        base_rul *= 0.6
    if vibration > 5.0:
        base_rul *= 0.5
    return max(round(base_rul, 2), 0.0)


def _mock_anomaly(features: np.ndarray) -> tuple[bool, float]:
    """Detection d'anomalie mock."""
    temp = features[0, 0]
    vibration = features[0, 1]

    score = 0.0
    if temp > alert_thresholds.temperature_critical:
        score -= 0.5
    if vibration > 5.0:
        score -= 0.3
    if temp < 10:
        score -= 0.2

    is_anomaly = score < -0.3
    return is_anomaly, round(score, 4)


def _anomaly_severity(score: float) -> str:
    """Determine la severite d'une anomalie a partir du score."""
    if score < -0.5:
        return "critical"
    if score < -0.2:
        return "warning"
    return "normal"


def _contributing_factors(data: AnomalyInput) -> list[str]:
    """Identifie les facteurs contribuant a une anomalie."""
    factors: list[str] = []
    if data.temperature > alert_thresholds.temperature_critical:
        factors.append("Temperature anormalement elevee")
    if data.vibration > 5.0:
        factors.append("Vibrations excessives")
    if data.energy_consumption > 200:
        factors.append("Consommation energetique elevee")
    if data.humidity > 80:
        factors.append("Humidite elevee")
    if data.pressure < 900 or data.pressure > 1100:
        factors.append("Pression hors plage normale")
    return factors


# ==============================================================================
# Lifespan (startup / shutdown)
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("MECHA API -- Demarrage en cours...")
    logger.info("Version : %s", API_VERSION)
    logger.info("Repertoire modeles : %s", MODEL_DIR.resolve())
    logger.info("=" * 60)

    models.load_all()

    if models.loaded:
        logger.info("API demarree avec modeles ML charges")
    else:
        logger.warning("API demarree en mode FALLBACK (modeles absents)")

    yield

    # --- Shutdown ---
    logger.info("MECHA API -- Arret en cours...")
    logger.info("Statistiques finales : %s", api_stats.to_dict())


# ==============================================================================
# Application FastAPI
# ==============================================================================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Equipe MECHA",
        "url": "https://github.com/MSPR2-MECHA",
    },
    license_info={
        "name": "Projet pedagogique EPSI",
    },
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Endpoints
# ==============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Monitoring"],
    summary="Health check de l'API",
)
async def health_check() -> HealthResponse:
    """Verifie l'etat de sante de l'API et la disponibilite des modeles."""
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        models_loaded=models.loaded,
        models_available={
            "classifier": models.classifier is not None,
            "xgboost": models.xgboost is not None,
            "isolation_forest": models.isolation_forest is not None,
            "rul_regressor": models.rul_regressor is not None,
        },
        uptime_seconds=round(time.time() - api_stats.start_time, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------- Prediction unitaire ----------

@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Predictions"],
    summary="Prediction de maintenance pour une machine",
)
async def predict(data: SensorInput) -> PredictionResponse:
    """Predit si une machine necessite une maintenance a partir des donnees capteur.

    Utilise le modele Random Forest en priorite, puis XGBoost en fallback.
    Si aucun modele n'est charge, utilise des heuristiques basees sur les seuils MECHA.
    """
    try:
        features = _extract_features(data)
        alerts = _evaluate_alerts(data)

        model_name = "fallback_heuristic"

        if models.classifier is not None:
            proba = models.classifier.predict_proba(features)
            prediction = int(np.argmax(proba, axis=1)[0])
            confidence = float(np.max(proba, axis=1)[0])
            model_name = "random_forest"
        elif models.xgboost is not None:
            proba = models.xgboost.predict_proba(features)
            prediction = int(np.argmax(proba, axis=1)[0])
            confidence = float(np.max(proba, axis=1)[0])
            model_name = "xgboost"
        else:
            prediction, confidence = _mock_predict(features)

        risk = _risk_level_from_confidence(confidence, prediction)
        label = "maintenance_required" if prediction == 1 else "normal"

        api_stats.total_predictions += 1
        logger.info(
            "Prediction : machine=%s result=%s confidence=%.3f model=%s",
            data.machine_id or "N/A",
            label,
            confidence,
            model_name,
        )

        return PredictionResponse(
            machine_id=data.machine_id,
            prediction=label,
            confidence=confidence,
            risk_level=risk,
            alerts=alerts,
            model_used=model_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as exc:
        api_stats.total_errors += 1
        logger.error("Erreur prediction : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prediction : {exc}",
        ) from exc


# ---------- Prediction batch ----------

@app.post(
    "/predict/batch",
    response_model=BatchResponse,
    tags=["Predictions"],
    summary="Prediction de maintenance en batch",
)
async def predict_batch(data: BatchInput) -> BatchResponse:
    """Execute des predictions sur un lot de machines (max 100)."""
    start = time.time()
    predictions: list[PredictionResponse] = []

    for machine_data in data.machines:
        result = await predict(machine_data)
        predictions.append(result)

    processing_ms = round((time.time() - start) * 1000, 2)
    api_stats.total_batch_predictions += 1

    logger.info(
        "Batch prediction : %d machines en %.1f ms",
        len(predictions),
        processing_ms,
    )

    return BatchResponse(
        predictions=predictions,
        total=len(predictions),
        processing_time_ms=processing_ms,
    )


# ---------- Prediction RUL ----------

@app.post(
    "/predict/rul",
    response_model=RULResponse,
    tags=["Predictions"],
    summary="Prediction du temps restant avant panne (RUL)",
)
async def predict_rul(data: RULInput) -> RULResponse:
    """Estime le Remaining Useful Life (RUL) d'une machine en heures.

    Utilise le modele RF Regressor entraine pour la regression RUL.
    """
    try:
        features = _extract_features(data)
        model_name = "fallback_heuristic"

        if models.rul_regressor is not None:
            rul_value = float(models.rul_regressor.predict(features)[0])
            rul_value = max(rul_value, 0.0)
            model_name = "rf_regressor_rul"
            # Estimation de confiance basee sur la plage de prediction des arbres
            if hasattr(models.rul_regressor, "estimators_"):
                tree_preds = [
                    est.predict(features)[0]
                    for est in models.rul_regressor.estimators_
                ]
                std = float(np.std(tree_preds))
                mean = float(np.mean(tree_preds))
                # Confiance inversement proportionnelle a la dispersion relative
                confidence = max(0.1, min(1.0, 1.0 - (std / (abs(mean) + 1))))
            else:
                confidence = 0.75
        else:
            rul_value = _mock_rul(features)
            confidence = 0.5

        category = _rul_category(rul_value)
        api_stats.total_rul_predictions += 1

        logger.info(
            "RUL prediction : machine=%s rul=%.1fh category=%s model=%s",
            data.machine_id or "N/A",
            rul_value,
            category,
            model_name,
        )

        return RULResponse(
            machine_id=data.machine_id,
            rul_hours=rul_value,
            rul_category=category,
            confidence=round(confidence, 4),
            model_used=model_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as exc:
        api_stats.total_errors += 1
        logger.error("Erreur prediction RUL : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prediction RUL : {exc}",
        ) from exc


# ---------- Detection d'anomalies ----------

@app.post(
    "/anomaly",
    response_model=AnomalyResponse,
    tags=["Anomalies"],
    summary="Detection d'anomalie (Isolation Forest)",
)
async def detect_anomaly(data: AnomalyInput) -> AnomalyResponse:
    """Detecte les anomalies dans les donnees capteur d'une machine.

    Utilise l'Isolation Forest pour identifier les comportements atypiques.
    Score negatif = plus anormal.
    """
    try:
        features = _extract_features(data)
        model_name = "fallback_heuristic"

        if models.isolation_forest is not None:
            raw_prediction = models.isolation_forest.predict(features)[0]
            anomaly_score = float(
                models.isolation_forest.decision_function(features)[0]
            )
            is_anomaly = raw_prediction == -1
            model_name = "isolation_forest"
        else:
            is_anomaly, anomaly_score = _mock_anomaly(features)

        severity = _anomaly_severity(anomaly_score)
        factors = _contributing_factors(data) if is_anomaly else []
        api_stats.total_anomaly_checks += 1

        logger.info(
            "Anomaly detection : machine=%s anomaly=%s score=%.3f severity=%s model=%s",
            data.machine_id or "N/A",
            is_anomaly,
            anomaly_score,
            severity,
            model_name,
        )

        return AnomalyResponse(
            machine_id=data.machine_id,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            severity=severity,
            contributing_factors=factors,
            model_used=model_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as exc:
        api_stats.total_errors += 1
        logger.error("Erreur detection anomalie : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la detection d'anomalie : {exc}",
        ) from exc


# ---------- Metriques ----------

@app.get(
    "/metrics",
    response_model=MetricsResponse,
    tags=["Monitoring"],
    summary="Metriques de performance des modeles et de l'API",
)
async def get_metrics() -> MetricsResponse:
    """Retourne les metriques de performance des modeles et les statistiques API.

    Les metriques des modeles sont des valeurs de reference issues de l'entrainement
    (MSPR 1 et objectifs MSPR 2).
    """
    model_metrics = {
        "random_forest": {
            "type": "classification",
            "status": "loaded" if models.classifier is not None else "not_loaded",
            "reference_metrics": {
                "f1_score_mspr1": 0.71,
                "target_f1_mspr2": 0.75,
                "accuracy": None,
                "precision": None,
                "recall": None,
            },
        },
        "xgboost": {
            "type": "classification",
            "status": "loaded" if models.xgboost is not None else "not_loaded",
            "reference_metrics": {
                "target_f1_mspr2": 0.75,
            },
        },
        "isolation_forest": {
            "type": "anomaly_detection",
            "status": "loaded" if models.isolation_forest is not None else "not_loaded",
            "reference_metrics": {
                "f1_score_mspr1": 0.38,
                "role": "complementary",
            },
        },
        "rf_regressor_rul": {
            "type": "regression",
            "status": "loaded" if models.rul_regressor is not None else "not_loaded",
            "reference_metrics": {
                "target_mae_minutes": 50,
            },
        },
    }

    return MetricsResponse(
        models=model_metrics,
        api_stats=api_stats.to_dict(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------- Model Info (model card resumee) ----------

@app.get(
    "/model-info",
    response_model=ModelInfoResponse,
    tags=["Monitoring"],
    summary="Informations des modeles (model card resumee)",
)
async def get_model_info() -> ModelInfoResponse:
    """Retourne les informations detaillees des modeles (model card EU AI Act).

    Inclut la description, le role, les limitations et la conformite
    reglementaire de chaque modele.
    """
    model_cards = [
        {
            "name": "Random Forest Classifier",
            "file": "random_forest.joblib",
            "loaded": models.classifier is not None,
            "role": "Classification de l'etat de maintenance (normal / a risque)",
            "algorithm": "Random Forest (scikit-learn)",
            "training_data": "Donnees capteurs machines MECHA (enrichies)",
            "input_features": ML_FEATURE_NAMES,
            "output": "Classe binaire + probabilite",
            "limitations": [
                "Entraine sur donnees simulees/enrichies",
                "Performance degradee sur machines non representees",
                "Necessite des features engineerees (rolling, trend)",
            ],
            "human_in_the_loop": True,
        },
        {
            "name": "XGBoost Classifier",
            "file": "xgboost_model.joblib",
            "loaded": models.xgboost is not None,
            "role": "Classification de maintenance (modele complementaire)",
            "algorithm": "XGBoost (gradient boosting)",
            "training_data": "Donnees capteurs machines MECHA (enrichies)",
            "input_features": ML_FEATURE_NAMES,
            "output": "Classe binaire + probabilite",
            "limitations": [
                "Sensible au sur-apprentissage sur petits jeux de donnees",
                "Hyperparametres a ajuster selon le volume de donnees",
            ],
            "human_in_the_loop": True,
        },
        {
            "name": "Isolation Forest",
            "file": "isolation_forest.joblib",
            "loaded": models.isolation_forest is not None,
            "role": "Detection de comportements atypiques des capteurs",
            "algorithm": "Isolation Forest (scikit-learn)",
            "training_data": "Donnees capteurs en fonctionnement normal",
            "input_features": ML_FEATURE_NAMES,
            "output": "Score d'anomalie + label (normal / anomalie)",
            "limitations": [
                "F1 faible en MSPR 1 (0.38) -- role complementaire",
                "Seuil de contamination a calibrer",
                "Ne distingue pas le type d'anomalie",
            ],
            "human_in_the_loop": True,
        },
        {
            "name": "RF Regressor RUL",
            "file": "rf_regressor_rul.joblib",
            "loaded": models.rul_regressor is not None,
            "role": "Estimation du temps restant avant defaillance (RUL)",
            "algorithm": "Random Forest Regressor (scikit-learn)",
            "training_data": "Donnees capteurs avec etiquettes RUL",
            "input_features": ML_FEATURE_NAMES,
            "output": "Valeur continue (heures restantes)",
            "limitations": [
                "Objectif MAE < 50 minutes",
                "Precision depend de la qualite des etiquettes RUL",
            ],
            "human_in_the_loop": True,
        },
    ]

    return ModelInfoResponse(
        project="MECHA -- Maintenance Predictive Industrielle",
        version=API_VERSION,
        models=model_cards,
        features=ML_FEATURE_NAMES,
        alert_thresholds=alert_thresholds.to_dict(),
        compliance={
            "eu_ai_act": "Human-in-the-Loop obligatoire, model cards fournies",
            "rgpd": "Donnees machine uniquement (pas de donnees personnelles)",
            "nis2": "Principes de cybersecurite respectes",
            "iec_62443": "Cloisonnement OT/IT documente",
        },
    )


# ---------- Configuration des alertes ----------

@app.get(
    "/alerts/config",
    response_model=AlertConfigResponse,
    tags=["Alertes"],
    summary="Configuration actuelle des seuils d'alerte",
)
async def get_alert_config() -> AlertConfigResponse:
    """Retourne les seuils d'alerte MECHA actuellement configures."""
    config = alert_thresholds.to_dict()
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    return AlertConfigResponse(**config)


@app.put(
    "/alerts/config",
    response_model=AlertConfigResponse,
    tags=["Alertes"],
    summary="Modifier les seuils d'alerte",
)
async def update_alert_config(data: AlertConfigInput) -> AlertConfigResponse:
    """Met a jour les seuils d'alerte MECHA.

    Seuls les champs fournis sont modifies, les autres conservent leur valeur.
    """
    updated_fields: list[str] = []

    if data.temperature_critical_celsius is not None:
        alert_thresholds.temperature_critical = data.temperature_critical_celsius
        updated_fields.append("temperature_critical_celsius")

    if data.rebuts_max_percent is not None:
        alert_thresholds.rebuts_max_percent = data.rebuts_max_percent
        updated_fields.append("rebuts_max_percent")

    if data.trs_min_percent is not None:
        alert_thresholds.trs_min_percent = data.trs_min_percent
        updated_fields.append("trs_min_percent")

    if data.cycle_deviation_max_percent is not None:
        alert_thresholds.cycle_deviation_max_percent = data.cycle_deviation_max_percent
        updated_fields.append("cycle_deviation_max_percent")

    if data.anomaly_rate_max_percent is not None:
        alert_thresholds.anomaly_rate_max_percent = data.anomaly_rate_max_percent
        updated_fields.append("anomaly_rate_max_percent")

    logger.info("Seuils d'alerte mis a jour : %s", updated_fields)

    config = alert_thresholds.to_dict()
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    return AlertConfigResponse(**config)


# ==============================================================================
# Point d'entree (developpement local)
# ==============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        log_level=LOG_LEVEL.lower(),
    )
