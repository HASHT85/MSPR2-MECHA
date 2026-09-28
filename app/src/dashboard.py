"""
MECHA - Dashboard de Maintenance Predictive Industrielle
========================================================
Interface metier pour les equipes maintenance et production de MECHA.
Permet de visualiser l'etat des machines, les predictions IA, les alertes
et les KPIs industriels en temps reel.

Auteur : Equipe MECHA
Date : Mai 2026
"""

import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ==============================================================================
# CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="MECHA - Pilotage Industriel IA",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10"))

# Features capteurs attendues par l'API (identiques a ML_FEATURE_NAMES cote API).
# Le RUL et le downtime_risk ne sont PAS envoyes : ce sont des sorties du modele.
API_FEATURES = [
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
API_REQUIRED = API_FEATURES[:5]


# ==============================================================================
# CLIENT API -- toutes les predictions IA passent par l'API REST
# ==============================================================================


def build_payload(row):
    """Construit le corps JSON attendu par l'API a partir d'une ligne capteur."""
    payload = {}
    for feat in API_FEATURES:
        val = row.get(feat)
        if val is None or pd.isna(val):
            if feat in API_REQUIRED:
                payload[feat] = 0.0
            continue
        payload[feat] = float(val)
    payload["machine_id"] = str(row.get("machine_id", ""))
    return payload


def api_get(path):
    """GET sur l'API. Retourne le JSON ou None si l'API est injoignable."""
    try:
        resp = requests.get(f"{API_URL}{path}", timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def api_post(path, payload):
    """POST sur l'API. Retourne le JSON ou None si l'API est injoignable."""
    try:
        resp = requests.post(f"{API_URL}{path}", json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


@st.cache_data(ttl=60)
def api_health():
    """Etat de l'API (cache 60 s)."""
    return api_get("/health")


@st.cache_data(ttl=60)
def api_metrics():
    return api_get("/metrics")


@st.cache_data(ttl=300)
def api_model_info():
    return api_get("/model-info")


def latest_rows(df):
    """Derniere mesure connue de chaque machine."""
    return df.sort_values("timestamp").groupby("machine_id").tail(1)


@st.cache_data(ttl=60)
def api_predict_batch(rows_json):
    """Predictions IA pour un lot de machines via POST /predict/batch.

    `rows_json` est la liste des payloads serialisee (hashable pour le cache).
    Retourne un DataFrame (machine_id, prediction, confidence, risk_level,
    model_used) ou None si l'API est indisponible.
    """
    payloads = json.loads(rows_json)
    results = []
    for start in range(0, len(payloads), 100):  # limite API : 100 machines
        chunk = payloads[start : start + 100]
        resp = api_post("/predict/batch", {"machines": chunk})
        if resp is None:
            return None
        results.extend(resp["predictions"])
    if not results:
        return None
    out = pd.DataFrame(results)[
        ["machine_id", "prediction", "confidence", "risk_level", "model_used"]
    ]
    out["machine_id"] = out["machine_id"].astype(int)
    # Probabilite de maintenance (0-1) : confiance orientee vers la classe positive
    out["proba_maintenance"] = np.where(
        out["prediction"] == "maintenance_required",
        out["confidence"],
        1 - out["confidence"],
    )
    return out


def get_ai_predictions(df):
    """Predictions IA (via API) pour la derniere mesure de chaque machine du df."""
    rows = latest_rows(df)
    payloads = [build_payload(row) for _, row in rows.iterrows()]
    return api_predict_batch(json.dumps(payloads))


def get_machine_diagnostic(row):
    """Diagnostic IA complet d'une machine : classification, RUL, anomalie."""
    payload = build_payload(row)
    return {
        "predict": api_post("/predict", payload),
        "rul": api_post("/predict/rul", payload),
        "anomaly": api_post("/anomaly", payload),
    }


# Couleurs theme industriel sombre
COLORS = {
    "primary": "#00D4FF",
    "secondary": "#7B61FF",
    "success": "#00E676",
    "warning": "#FFB300",
    "danger": "#FF5252",
    "background": "#0E1117",
    "card_bg": "#1E2028",
    "text": "#FAFAFA",
    "text_muted": "#8B8D97",
    "gradient_start": "#667eea",
    "gradient_end": "#764ba2",
}

USINE_COLORS = {
    "USN-FR-01": "#00D4FF",
    "USN-FR-02": "#7B61FF",
    "USN-FR-03": "#00E676",
    "USN-ES-01": "#FFB300",
    "USN-ES-02": "#FF5252",
}

USINE_NOMS = {
    "USN-FR-01": "Lyon (FR)",
    "USN-FR-02": "Toulouse (FR)",
    "USN-FR-03": "Nantes (FR)",
    "USN-ES-01": "Barcelone (ES)",
    "USN-ES-02": "Madrid (ES)",
}

# Seuils d'alerte MECHA
SEUILS = {
    "temp_critique": 100,
    "vibr_critique": 70,
    "rul_critique": 50,
    "trs_min": 75,
    "rebuts_max": 3.0,
    "anomaly_max": 10,
}


# ==============================================================================
# STYLES CSS
# ==============================================================================


def apply_custom_css():
    st.markdown(
        """
    <style>
        /* Theme sombre industriel */
        .stApp {
            background-color: #0E1117;
        }
        
        /* Cards metriques */
        .metric-card {
            background: linear-gradient(135deg, #1a1c2e 0%, #2a2d42 100%);
            border-radius: 16px;
            padding: 20px 24px;
            margin: 8px 0;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0,212,255,0.15);
        }
        .metric-label {
            color: #8B8D97;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, #00D4FF, #7B61FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        }
        .metric-value.success { background: linear-gradient(135deg, #00E676, #00D4FF); -webkit-background-clip: text; }
        .metric-value.warning { background: linear-gradient(135deg, #FFB300, #FF8F00); -webkit-background-clip: text; }
        .metric-value.danger { background: linear-gradient(135deg, #FF5252, #FF1744); -webkit-background-clip: text; }
        .metric-delta {
            color: #8B8D97;
            font-size: 12px;
            margin-top: 4px;
        }
        
        /* Header */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            color: white;
        }
        .main-header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }
        .main-header p {
            margin: 4px 0 0 0;
            opacity: 0.85;
            font-size: 14px;
        }
        
        /* Alertes */
        .alert-card {
            border-radius: 12px;
            padding: 16px 20px;
            margin: 6px 0;
            border-left: 4px solid;
        }
        .alert-critical {
            background: rgba(255,82,82,0.1);
            border-color: #FF5252;
        }
        .alert-major {
            background: rgba(255,179,0,0.1);
            border-color: #FFB300;
        }
        .alert-info {
            background: rgba(0,212,255,0.1);
            border-color: #00D4FF;
        }
        
        /* Sidebar */
        .css-1d391kg { background-color: #151821; }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #1E2028;
            border-radius: 8px;
            padding: 8px 16px;
            color: #8B8D97;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# CHARGEMENT DES DONNEES
# ==============================================================================


@st.cache_data(ttl=300)
def load_data():
    """Charge le dataset MECHA depuis le fichier CSV."""
    # Chemins possibles selon l'environnement (local ou Docker)
    possible_paths = [
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "processed",
            "mecha_dataset_processed.csv",
        ),
        # Docker: data monte dans /app/data
        "/app/data/processed/mecha_dataset_processed.csv",
        # Docker: merged dataset
        "/app/data/raw/mecha_merged_dataset.csv",
        # Chemins relatifs locaux
        "data/processed/mecha_dataset_processed.csv",
        "../data/processed/mecha_dataset_processed.csv",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["timestamp"], low_memory=False)
            return df

    st.error(
        "Dataset non trouve. Executez d'abord : python data/scripts/generate_data.py && python data/scripts/merge_datasets.py"
    )
    return None


@st.cache_data(ttl=300)
def load_model_metrics():
    """Charge les metriques des modeles ML."""
    possible_paths = [
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models",
            "evaluation",
            "results",
            "all_models_metrics.json",
        ),
        "/app/models/evaluation/results/all_models_metrics.json",
        "models/evaluation/results/all_models_metrics.json",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    return None


# ==============================================================================
# COMPOSANTS UI
# ==============================================================================


def render_metric_card(label, value, delta=None, color_class=""):
    """Affiche une carte metrique stylisee."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{value}</div>
        {delta_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_alert(message, level="info", machine=None, usine=None):
    """Affiche une alerte stylisee."""
    prefix = f"[{usine}] Machine {machine} - " if machine and usine else ""
    st.markdown(
        f"""
    <div class="alert-card alert-{level}">
        <strong>{prefix}{message}</strong>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# PAGES
# ==============================================================================


def page_groupe(df):
    """Vue Groupe - KPIs globaux des 5 usines (Direction generale)."""

    st.markdown(
        """
    <div class="main-header">
        <h1>Dashboard Groupe - MECHA</h1>
        <p>Vue consolidee des 5 usines | Direction Generale & Direction Industrielle</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # KPIs globaux
    col1, col2, col3, col4, col5 = st.columns(5)

    total_machines = df["machine_id"].nunique()
    machines_ok = df[df["machine_status"] == 1]["machine_id"].nunique()
    machines_panne = df[df["machine_status"] == 2]["machine_id"].nunique()
    trs_global = (machines_ok / total_machines * 100) if total_machines > 0 else 0
    taux_anomalies = df["anomaly_flag"].mean() * 100

    with col1:
        color = (
            "success"
            if trs_global >= 75
            else "warning"
            if trs_global >= 60
            else "danger"
        )
        render_metric_card("TRS Global", f"{trs_global:.1f}%", "Objectif: > 75%", color)
    with col2:
        taux_maint = df["maintenance_required"].mean() * 100
        color = (
            "success" if taux_maint < 5 else "warning" if taux_maint < 15 else "danger"
        )
        render_metric_card(
            "Taux Maintenance",
            f"{taux_maint:.1f}%",
            f"{int(df['maintenance_required'].sum())} interventions",
            color,
        )
    with col3:
        color = (
            "success"
            if taux_anomalies < 5
            else "warning"
            if taux_anomalies < 10
            else "danger"
        )
        render_metric_card(
            "Anomalies",
            f"{taux_anomalies:.1f}%",
            f"Seuil: < {SEUILS['anomaly_max']}%",
            color,
        )
    with col4:
        render_metric_card(
            "Machines Actives",
            f"{machines_ok}/{total_machines}",
            f"{machines_panne} en panne",
        )
    with col5:
        rul_moyen = df[df["machine_status"] == 1]["predicted_remaining_life"].mean()
        render_metric_card(
            "RUL Moyen", f"{rul_moyen:.0f} min", "Duree de vie residuelle"
        )

    st.markdown("---")

    # Graphiques
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Performance par Usine")
        usine_stats = (
            df.groupby("usine_id")
            .agg(
                {
                    "maintenance_required": "mean",
                    "anomaly_flag": "mean",
                    "temperature": "mean",
                    "predicted_remaining_life": "mean",
                }
            )
            .reset_index()
        )
        usine_stats["usine_nom"] = usine_stats["usine_id"].map(USINE_NOMS)
        usine_stats["maintenance_pct"] = usine_stats["maintenance_required"] * 100
        usine_stats["anomaly_pct"] = usine_stats["anomaly_flag"] * 100

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=usine_stats["usine_nom"],
                y=usine_stats["maintenance_pct"],
                name="Maintenance (%)",
                marker_color="#FF5252",
            )
        )
        fig.add_trace(
            go.Bar(
                x=usine_stats["usine_nom"],
                y=usine_stats["anomaly_pct"],
                name="Anomalies (%)",
                marker_color="#FFB300",
            )
        )
        fig.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            margin=dict(t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Distribution des Types de Pannes")
        failure_counts = df[df["failure_type"] != "Normal"][
            "failure_type"
        ].value_counts()
        if len(failure_counts) > 0:
            fig = px.pie(
                values=failure_counts.values,
                names=failure_counts.index,
                color_discrete_sequence=[
                    "#FF5252",
                    "#FFB300",
                    "#00D4FF",
                    "#7B61FF",
                    "#00E676",
                ],
                hole=0.5,
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=400,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune panne detectee dans la periode.")

    # Heatmap temperature par machine et usine
    st.subheader("Carte Thermique - Temperature Moyenne par Machine")
    temp_by_machine = (
        df.groupby(["usine_id", "machine_id"])["temperature"].mean().reset_index()
    )
    temp_by_machine["usine_nom"] = temp_by_machine["usine_id"].map(USINE_NOMS)

    fig = px.scatter(
        temp_by_machine,
        x="machine_id",
        y="usine_nom",
        size="temperature",
        color="temperature",
        color_continuous_scale="RdYlGn_r",
        range_color=[60, 100],
        labels={
            "temperature": "Temp. (C)",
            "machine_id": "Machine ID",
            "usine_nom": "Usine",
        },
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def page_site(df):
    """Vue Site - Detail par usine."""

    st.markdown(
        """
    <div class="main-header">
        <h1>Dashboard Site - MECHA</h1>
        <p>Vue operationnelle par usine | Directeur de site & Responsable production</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Selection usine
    usine_selection = st.selectbox(
        "Selectionner une usine",
        options=list(USINE_NOMS.keys()),
        format_func=lambda x: USINE_NOMS[x],
    )

    df_usine = df[df["usine_id"] == usine_selection]

    # KPIs site
    col1, col2, col3, col4 = st.columns(4)

    machines_usine = df_usine["machine_id"].nunique()
    machines_fonctionnelles = df_usine[df_usine["machine_status"] == 1][
        "machine_id"
    ].nunique()

    with col1:
        trs = (
            machines_fonctionnelles / machines_usine * 100 if machines_usine > 0 else 0
        )
        color = "success" if trs >= 75 else "warning" if trs >= 60 else "danger"
        render_metric_card(
            "TRS Site",
            f"{trs:.1f}%",
            f"{machines_fonctionnelles}/{machines_usine} machines",
            color,
        )
    with col2:
        temp_moy = df_usine[df_usine["machine_status"] == 1]["temperature"].mean()
        color = (
            "success" if temp_moy < 85 else "warning" if temp_moy < 100 else "danger"
        )
        render_metric_card(
            "Temp. Moyenne",
            f"{temp_moy:.1f} C",
            f"Seuil: < {SEUILS['temp_critique']}C",
            color,
        )
    with col3:
        maint_pct = df_usine["maintenance_required"].mean() * 100
        render_metric_card(
            "Maintenance Req.",
            f"{maint_pct:.1f}%",
            f"{int(df_usine['maintenance_required'].sum())} interventions",
        )
    with col4:
        rul_min = df_usine[df_usine["machine_status"] == 1][
            "predicted_remaining_life"
        ].min()
        color = (
            "danger"
            if rul_min < SEUILS["rul_critique"]
            else "warning"
            if rul_min < 150
            else "success"
        )
        render_metric_card(
            "RUL Minimum", f"{rul_min:.0f} min", "Machine la plus critique", color
        )

    st.markdown("---")

    # Etat des machines
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Etat des Machines")
        machine_status = (
            df_usine.groupby("machine_id")
            .agg(
                {
                    "temperature": "last",
                    "vibration": "last",
                    "predicted_remaining_life": "last",
                    "machine_status": "last",
                    "maintenance_required": "last",
                    "machine_profile": "first",
                    "downtime_risk": "last",
                }
            )
            .reset_index()
        )

        # Indicateur d'etat
        status_map = {0: "Arret", 1: "OK", 2: "PANNE"}
        machine_status["etat"] = machine_status["machine_status"].map(status_map)

        # Prediction IA via l'API (derniere mesure de chaque machine)
        ai_preds = get_ai_predictions(df_usine)
        if ai_preds is not None:
            machine_status = machine_status.merge(
                ai_preds[["machine_id", "prediction", "proba_maintenance"]],
                on="machine_id",
                how="left",
            )
            machine_status["ia"] = np.where(
                machine_status["prediction"] == "maintenance_required",
                "MAINTENANCE",
                "normal",
            )
            risque_col = machine_status["proba_maintenance"].round(2)
            risque_label = "Proba. IA"
        else:
            machine_status["ia"] = "API indispo."
            risque_col = machine_status["downtime_risk"].round(2)
            risque_label = "Risque (hist.)"

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=[
                            "Machine",
                            "Profil",
                            "Etat",
                            "Temp (C)",
                            "Vibr.",
                            "RUL (min)",
                            risque_label,
                            "Prediction IA",
                        ],
                        fill_color="#1E2028",
                        font=dict(color="white", size=13),
                        align="center",
                    ),
                    cells=dict(
                        values=[
                            machine_status["machine_id"],
                            machine_status["machine_profile"],
                            machine_status["etat"],
                            machine_status["temperature"].round(1),
                            machine_status["vibration"].round(1),
                            machine_status["predicted_remaining_life"].astype(int),
                            risque_col,
                            machine_status["ia"],
                        ],
                        fill_color=[["#1a1c2e"] * len(machine_status)],
                        font=dict(color="white", size=12),
                        align="center",
                    ),
                )
            ]
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Alertes Actives")
        # Alertes temperature
        machines_hot = df_usine[df_usine["temperature"] > SEUILS["temp_critique"]][
            "machine_id"
        ].unique()
        for m in machines_hot[:5]:
            render_alert(
                f"Temperature critique (> {SEUILS['temp_critique']}C)",
                "critical",
                m,
                usine_selection,
            )

        # Alertes RUL
        machines_rul = df_usine[
            (df_usine["predicted_remaining_life"] < SEUILS["rul_critique"])
            & (df_usine["machine_status"] == 1)
        ]["machine_id"].unique()
        for m in machines_rul[:5]:
            render_alert(
                f"RUL critique (< {SEUILS['rul_critique']} min)",
                "major",
                m,
                usine_selection,
            )

        # Alertes IA : maintenance predite par le modele (via API)
        machines_ia = []
        if ai_preds is not None:
            machines_ia = ai_preds[ai_preds["prediction"] == "maintenance_required"][
                "machine_id"
            ].tolist()
        for m in machines_ia[:5]:
            proba = ai_preds.loc[ai_preds["machine_id"] == m, "proba_maintenance"]
            render_alert(
                f"Maintenance predite par l'IA (proba. {float(proba.iloc[0]):.0%})",
                "major",
                m,
                usine_selection,
            )

        if len(machines_hot) == 0 and len(machines_rul) == 0 and not machines_ia:
            render_alert("Aucune alerte active", "info")

    # Graphique tendance temperature
    st.subheader("Tendance Temperature par Machine")
    selected_machines = st.multiselect(
        "Machines a afficher",
        options=sorted(df_usine["machine_id"].unique()),
        default=sorted(df_usine["machine_id"].unique())[:3],
    )

    if selected_machines:
        df_plot = df_usine[df_usine["machine_id"].isin(selected_machines)]
        fig = px.line(
            df_plot,
            x="timestamp",
            y="temperature",
            color="machine_id",
            labels={
                "temperature": "Temperature (C)",
                "timestamp": "Temps",
                "machine_id": "Machine",
            },
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.add_hline(
            y=SEUILS["temp_critique"],
            line_dash="dash",
            line_color="#FF5252",
            annotation_text=f"Seuil critique ({SEUILS['temp_critique']}C)",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            margin=dict(t=30, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)


def page_machine(df):
    """Vue Machine - Detail individuel."""

    st.markdown(
        """
    <div class="main-header">
        <h1>Vue Machine - MECHA</h1>
        <p>Diagnostic individuel | Equipe maintenance & Data team</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        machine_id = st.selectbox("Machine", sorted(df["machine_id"].unique()))

    df_machine = df[df["machine_id"] == machine_id]

    with col2:
        usine = df_machine["usine_id"].iloc[0] if len(df_machine) > 0 else "N/A"
        profile = (
            df_machine["machine_profile"].iloc[0] if len(df_machine) > 0 else "N/A"
        )
        st.info(
            f"Usine: **{USINE_NOMS.get(usine, usine)}** | Profil: **{profile}** | "
            f"Ligne: **{df_machine['ligne_production'].iloc[0]}** | "
            f"Piece: **{df_machine['type_piece'].iloc[0]}**"
        )

    # KPIs machine
    col1, col2, col3, col4, col5 = st.columns(5)
    last = df_machine.iloc[-1] if len(df_machine) > 0 else {}

    # Diagnostic IA (appels API sur la derniere mesure)
    diag = get_machine_diagnostic(last) if len(df_machine) > 0 else {}
    pred = diag.get("predict")
    if pred is not None:
        proba_ia = (
            pred["confidence"]
            if pred["prediction"] == "maintenance_required"
            else 1 - pred["confidence"]
        )
    else:
        proba_ia = None

    with col1:
        temp = last.get("temperature", 0)
        color = "success" if temp < 85 else "warning" if temp < 100 else "danger"
        render_metric_card("Temperature", f"{temp:.1f} C", "", color)
    with col2:
        vibr = last.get("vibration", 0)
        color = "success" if vibr < 50 else "warning" if vibr < 70 else "danger"
        render_metric_card("Vibration", f"{vibr:.1f}", "", color)
    with col3:
        rul = last.get("predicted_remaining_life", 0)
        color = "success" if rul > 200 else "warning" if rul > 50 else "danger"
        render_metric_card("RUL", f"{rul:.0f} min", "", color)
    with col4:
        if proba_ia is not None:
            color = (
                "success"
                if proba_ia < 0.3
                else "warning"
                if proba_ia < 0.6
                else "danger"
            )
            render_metric_card(
                "Risque IA (API)", f"{proba_ia:.1%}", pred["model_used"], color
            )
        else:
            risk = last.get("downtime_risk", 0)
            color = "success" if risk < 0.3 else "warning" if risk < 0.6 else "danger"
            render_metric_card("Risque (hist.)", f"{risk:.1%}", "API indispo.", color)
    with col5:
        status_map = {0: "Arret", 1: "OK", 2: "PANNE"}
        status = last.get("machine_status", 0)
        color = "success" if status == 1 else "danger" if status == 2 else "warning"
        render_metric_card("Statut", status_map.get(status, "?"), "", color)

    st.markdown("---")

    # Graphiques capteurs
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Capteurs en Temps Reel")
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            subplot_titles=("Temperature (C)", "Vibration (mm/s)", "RUL (min)"),
            vertical_spacing=0.08,
        )

        fig.add_trace(
            go.Scatter(
                x=df_machine["timestamp"],
                y=df_machine["temperature"],
                mode="lines",
                name="Temperature",
                line=dict(color="#FF5252"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df_machine["timestamp"],
                y=df_machine["temp_rolling_10min"],
                mode="lines",
                name="Moy. Mobile 10min",
                line=dict(color="#FFB300", dash="dash"),
            ),
            row=1,
            col=1,
        )
        fig.add_hline(
            y=SEUILS["temp_critique"],
            line_dash="dot",
            line_color="#FF5252",
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df_machine["timestamp"],
                y=df_machine["vibration"],
                mode="lines",
                name="Vibration",
                line=dict(color="#00D4FF"),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df_machine["timestamp"],
                y=df_machine["vibr_rolling_10min"],
                mode="lines",
                name="Moy. Mobile 10min",
                line=dict(color="#7B61FF", dash="dash"),
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df_machine["timestamp"],
                y=df_machine["predicted_remaining_life"],
                mode="lines",
                name="RUL",
                line=dict(color="#00E676"),
                fill="tozeroy",
                fillcolor="rgba(0,230,118,0.1)",
            ),
            row=3,
            col=1,
        )
        fig.add_hline(
            y=SEUILS["rul_critique"],
            line_dash="dot",
            line_color="#FFB300",
            row=3,
            col=1,
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=600,
            margin=dict(t=40, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Indicateurs de Risque")

        # Jauge de risque : probabilite de maintenance predite par l'API
        if proba_ia is not None:
            risk_val = proba_ia
            gauge_title = "Probabilite de maintenance -- IA (%)"
        else:
            risk_val = last.get("downtime_risk", 0)
            gauge_title = "Score de risque historique (%)"
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=risk_val * 100,
                title={"text": gauge_title},
                delta={"reference": 30},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#00D4FF"},
                    "steps": [
                        {"range": [0, 30], "color": "rgba(0,230,118,0.2)"},
                        {"range": [30, 60], "color": "rgba(255,179,0,0.2)"},
                        {"range": [60, 100], "color": "rgba(255,82,82,0.2)"},
                    ],
                    "threshold": {
                        "line": {"color": "#FF5252", "width": 4},
                        "thickness": 0.75,
                        "value": 60,
                    },
                },
            )
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
            margin=dict(t=60, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Diagnostic IA detaille (RUL + anomalie via API)
        st.subheader("Diagnostic IA (API)")
        rul_resp = diag.get("rul")
        ano_resp = diag.get("anomaly")
        if rul_resp is None and ano_resp is None:
            st.warning(f"API IA indisponible ({API_URL}) : diagnostic non calcule.")
        else:
            c_rul, c_ano = st.columns(2)
            with c_rul:
                if rul_resp:
                    cat = rul_resp["rul_category"]
                    color = {
                        "urgent": "danger",
                        "soon": "warning",
                        "moderate": "",
                        "safe": "success",
                    }.get(cat, "")
                    render_metric_card(
                        "RUL predit",
                        f"{rul_resp['rul_minutes']:.0f} min",
                        f"{cat} | confiance {rul_resp['confidence']:.0%}",
                        color,
                    )
            with c_ano:
                if ano_resp:
                    sev = ano_resp["severity"]
                    color = {"critical": "danger", "warning": "warning"}.get(
                        sev, "success"
                    )
                    render_metric_card(
                        "Anomalie",
                        "OUI" if ano_resp["is_anomaly"] else "non",
                        f"{sev} | score {ano_resp['anomaly_score']:.3f}",
                        color,
                    )
            if ano_resp and ano_resp.get("contributing_factors"):
                for factor in ano_resp["contributing_factors"]:
                    render_alert(factor, "major")
            if pred and pred.get("alerts"):
                for alert in pred["alerts"]:
                    render_alert(alert, "critical")

        # Feature importance (si disponible)
        st.subheader("Facteurs de Risque")
        features = {
            "Temperature": last.get("temperature", 0) / 120,
            "Vibration": last.get("vibration", 0) / 100,
            "RUL (inverse)": 1 - last.get("predicted_remaining_life", 500) / 500,
            "Energie": last.get("energy_consumption", 0) / 7,
            "Trend Temp.": max(0, last.get("temp_trend_1h", 0) * 10),
        }

        fig = go.Figure(
            go.Bar(
                x=list(features.values()),
                y=list(features.keys()),
                orientation="h",
                marker_color=[
                    "#FF5252" if v > 0.7 else "#FFB300" if v > 0.4 else "#00E676"
                    for v in features.values()
                ],
            )
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=250,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Niveau de risque normalise",
        )
        st.plotly_chart(fig, use_container_width=True)


def page_alertes(df):
    """Vue Alertes - Historique et filtre."""

    st.markdown(
        """
    <div class="main-header">
        <h1>Centre d'Alertes - MECHA</h1>
        <p>Suivi des alertes et anomalies | Tous niveaux</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        usine_filter = st.multiselect(
            "Filtrer par usine",
            list(USINE_NOMS.keys()),
            format_func=lambda x: USINE_NOMS[x],
        )
    with col2:
        type_filter = st.multiselect(
            "Type d'alerte",
            ["Temperature critique", "RUL critique", "Prediction IA", "Panne"],
        )
    with col3:
        profil_filter = st.multiselect("Profil machine", df["machine_profile"].unique())

    # Appliquer filtres
    df_filtered = df.copy()
    if usine_filter:
        df_filtered = df_filtered[df_filtered["usine_id"].isin(usine_filter)]
    if profil_filter:
        df_filtered = df_filtered[df_filtered["machine_profile"].isin(profil_filter)]

    # Generer les alertes
    alertes = []

    # Alertes temperature
    temp_alerts = df_filtered[df_filtered["temperature"] > SEUILS["temp_critique"]]
    for _, row in temp_alerts.head(20).iterrows():
        alertes.append(
            {
                "timestamp": row["timestamp"],
                "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
                "machine": row["machine_id"],
                "type": "Temperature critique",
                "niveau": "CRITIQUE",
                "detail": f"Temperature: {row['temperature']:.1f}C (seuil: {SEUILS['temp_critique']}C)",
            }
        )

    # Alertes RUL
    rul_alerts = df_filtered[
        (df_filtered["predicted_remaining_life"] < SEUILS["rul_critique"])
        & (df_filtered["machine_status"] == 1)
    ]
    for _, row in rul_alerts.head(20).iterrows():
        alertes.append(
            {
                "timestamp": row["timestamp"],
                "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
                "machine": row["machine_id"],
                "type": "RUL critique",
                "niveau": "MAJEUR",
                "detail": f"RUL: {row['predicted_remaining_life']:.0f} min (seuil: {SEUILS['rul_critique']} min)",
            }
        )

    # Alertes pannes
    panne_alerts = df_filtered[df_filtered["machine_status"] == 2]
    for _, row in panne_alerts.head(20).iterrows():
        alertes.append(
            {
                "timestamp": row["timestamp"],
                "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
                "machine": row["machine_id"],
                "type": "Panne",
                "niveau": "CRITIQUE",
                "detail": f"Type: {row['failure_type']}",
            }
        )

    # Alertes IA : maintenance predite par l'API sur la derniere mesure
    ai_preds = get_ai_predictions(df_filtered)
    if ai_preds is None:
        st.warning(f"API IA indisponible ({API_URL}) : alertes IA non calculees.")
    else:
        last_rows = latest_rows(df_filtered).set_index("machine_id")
        ia_alerts = ai_preds[ai_preds["prediction"] == "maintenance_required"]
        for _, row in ia_alerts.iterrows():
            src = last_rows.loc[row["machine_id"]]
            alertes.append(
                {
                    "timestamp": src["timestamp"],
                    "usine": USINE_NOMS.get(src["usine_id"], src["usine_id"]),
                    "machine": row["machine_id"],
                    "type": "Prediction IA",
                    "niveau": "MAJEUR"
                    if row["risk_level"] != "critical"
                    else "CRITIQUE",
                    "detail": (
                        f"Maintenance predite ({row['model_used']}), "
                        f"proba. {row['proba_maintenance']:.0%}, risque {row['risk_level']}"
                    ),
                }
            )

    # Filtre par type d'alerte (selection utilisateur)
    if type_filter:
        alertes = [a for a in alertes if a["type"] in type_filter]

    # Afficher les alertes
    if alertes:
        df_alertes = pd.DataFrame(alertes).sort_values("timestamp", ascending=False)

        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            critiques = len(df_alertes[df_alertes["niveau"] == "CRITIQUE"])
            render_metric_card(
                "Alertes Critiques",
                str(critiques),
                "",
                "danger" if critiques > 0 else "success",
            )
        with col2:
            majeurs = len(df_alertes[df_alertes["niveau"] == "MAJEUR"])
            render_metric_card(
                "Alertes Majeures",
                str(majeurs),
                "",
                "warning" if majeurs > 0 else "success",
            )
        with col3:
            render_metric_card("Total Alertes", str(len(df_alertes)), "")

        st.markdown("---")

        # Tableau
        st.dataframe(
            df_alertes,
            use_container_width=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Date/Heure"),
                "niveau": st.column_config.TextColumn("Niveau"),
            },
            hide_index=True,
        )
    else:
        st.success("Aucune alerte active !")


def page_modele(df):
    """Vue Modele - Performance et details du modele IA."""

    st.markdown(
        """
    <div class="main-header">
        <h1>Performance du Modele IA - MECHA</h1>
        <p>Suivi des metriques ML | Data team & Direction industrielle</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Etat des modeles charges par l'API
    health = api_health()
    st.subheader("Modeles charges par l'API")
    if health:
        cols = st.columns(4)
        for col, (name, ok) in zip(cols, health["models_available"].items()):
            with col:
                render_metric_card(
                    name.replace("_", " "),
                    "charge" if ok else "absent",
                    "",
                    "success" if ok else "danger",
                )
    else:
        st.warning(f"API IA indisponible ({API_URL}).")

    # Metriques d'entrainement : via l'API, sinon fichier local
    api_m = api_metrics()
    metrics = None
    source_label = ""
    if api_m and any(m.get("trained_metrics") for m in api_m["models"].values()):
        metrics = {
            k: v["trained_metrics"]
            for k, v in api_m["models"].items()
            if v.get("trained_metrics")
        }
        source_label = "source : API /metrics"
    else:
        local = load_model_metrics()
        if local:
            metrics = local.get("models", local)
            source_label = "source : fichier all_models_metrics.json"

    if metrics:
        # Comparaison des modeles
        st.subheader("Comparaison des Modeles")
        st.caption(source_label)
        cols = [
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "auc_roc",
            "mae",
            "r2_score",
        ]
        models_df = pd.DataFrame(metrics).T
        models_df = models_df[[c for c in cols if c in models_df.columns]]
        st.dataframe(models_df.astype(float).round(4), use_container_width=True)

        # Ventilation par source de donnees (simule vs reel AI4I)
        per_source = {
            k: v["per_source"] for k, v in metrics.items() if v.get("per_source")
        }
        if per_source:
            st.subheader("Performance par source de donnees (simule vs reel)")
            rows = []
            for model_name, sources in per_source.items():
                for src, m in sources.items():
                    rows.append({"modele": model_name, "source": src, **m})
            st.dataframe(
                pd.DataFrame(rows).round(3), use_container_width=True, hide_index=True
            )
    else:
        st.warning(
            "Metriques non disponibles. Executez d'abord : python models/training/train_models.py"
        )

        # Afficher les metriques de la MSPR 1 comme reference
        st.subheader("Metriques de reference (MSPR 1)")
        ref_data = {
            "Modele": ["Random Forest", "Regression Logistique", "Isolation Forest"],
            "Accuracy": [91.0, 70.1, 75.2],
            "Precision": [100.0, 36.4, 37.9],
            "Recall": [55.0, 67.2, 38.6],
            "F1-Score": [71.0, 47.2, 38.2],
            "AUC-ROC": [0.776, 0.761, None],
        }
        st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Analyse du dataset
    st.subheader("Analyse du Dataset")
    col1, col2 = st.columns(2)

    with col1:
        # Distribution variable cible
        target_counts = df["maintenance_required"].value_counts()
        fig = px.pie(
            values=target_counts.values,
            names=["Pas de maintenance", "Maintenance requise"],
            color_discrete_sequence=["#00E676", "#FF5252"],
            hole=0.5,
            title="Distribution Variable Cible (maintenance_required)",
        )
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Correlation features
        feature_cols = [
            "temperature",
            "vibration",
            "humidity",
            "pressure",
            "energy_consumption",
            "predicted_remaining_life",
        ]
        available_cols = [c for c in feature_cols if c in df.columns]
        corr = (
            df[available_cols + ["maintenance_required"]]
            .corr()["maintenance_required"]
            .drop("maintenance_required")
        )

        fig = go.Figure(
            go.Bar(
                x=corr.values,
                y=corr.index,
                orientation="h",
                marker_color=[
                    COLORS["danger"]
                    if abs(v) > 0.2
                    else COLORS["warning"]
                    if abs(v) > 0.05
                    else COLORS["text_muted"]
                    for v in corr.values
                ],
            )
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Correlation des Features avec maintenance_required",
            height=350,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Distribution profils machines
    st.subheader("Distribution par Profil de Machine")
    profile_stats = (
        df.groupby("machine_profile")
        .agg(
            {
                "maintenance_required": "mean",
                "temperature": "mean",
                "machine_id": "nunique",
            }
        )
        .reset_index()
    )
    profile_stats["maintenance_pct"] = profile_stats["maintenance_required"] * 100

    fig = px.bar(
        profile_stats,
        x="machine_profile",
        y="maintenance_pct",
        color="temperature",
        color_continuous_scale="RdYlGn_r",
        labels={
            "maintenance_pct": "Taux maintenance (%)",
            "machine_profile": "Profil",
            "temperature": "Temp. moy.",
        },
        text="machine_id",
    )
    fig.update_traces(texttemplate="%{text} machines", textposition="outside")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Human-in-the-Loop notice
    st.markdown("---")
    st.info("""
    **Conformite EU AI Act** : Ce systeme fonctionne en mode **Human-in-the-Loop**. 
    Les predictions de l'IA sont des **recommandations** et non des ordres automatiques. 
    Toute action de maintenance doit etre validee par un operateur humain qualifie.
    """)


# ==============================================================================
# APPLICATION PRINCIPALE
# ==============================================================================


def main():
    apply_custom_css()

    # Sidebar
    with st.sidebar:
        st.markdown("## MECHA")
        st.markdown("*Pilotage Industriel IA*")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["Groupe", "Site", "Machine", "Alertes", "Modele IA"],
            index=0,
        )

        st.markdown("---")
        st.markdown("### Parametres")
        auto_refresh = st.checkbox("Auto-refresh (5 min)", value=False)
        if auto_refresh:
            # Rechargement automatique de la page toutes les 5 minutes
            st.markdown(
                '<meta http-equiv="refresh" content="300">', unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("### A propos")
        st.caption("MSPR 2 - Bloc 4")
        st.caption("Equipe MECHA")
        st.caption(f"Derniere maj: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        st.markdown("---")
        st.markdown("### API IA")
        health = api_health()
        if health and health.get("models_loaded"):
            n_models = sum(1 for v in health["models_available"].values() if v)
            st.caption(f"Connectee : {n_models} modeles charges")
        elif health:
            st.caption("Connectee : MODE MOCK (modeles absents)")
        else:
            st.caption(f"Indisponible ({API_URL})")
            st.caption("Predictions IA desactivees")

        st.markdown("---")
        st.markdown("### Conformite")
        st.caption("Human-in-the-Loop: ACTIF")
        st.caption("EU AI Act: CONFORME")
        st.caption("RGPD: Donnees machine uniquement")

    # Chargement donnees
    df = load_data()

    if df is None:
        return

    # Routage
    if page == "Groupe":
        page_groupe(df)
    elif page == "Site":
        page_site(df)
    elif page == "Machine":
        page_machine(df)
    elif page == "Alertes":
        page_alertes(df)
    elif page == "Modele IA":
        page_modele(df)


if __name__ == "__main__":
    main()
