"""
MECHA - Dashboard de Maintenance Predictive Industrielle
========================================================
Interface metier pour les equipes maintenance et production de MECHA.
Permet de visualiser l'etat des machines, les predictions IA, les alertes
et les KPIs industriels en temps reel.

Auteur : Equipe MECHA
Date : Mai 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import requests
from datetime import datetime

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
    st.markdown("""
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
    """, unsafe_allow_html=True)


# ==============================================================================
# CHARGEMENT DES DONNEES
# ==============================================================================

@st.cache_data(ttl=300)
def load_data():
    """Charge le dataset MECHA depuis le fichier CSV."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "processed", "mecha_dataset_processed.csv"
    )
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=["timestamp"])
        return df
    
    # Fallback: chercher dans d'autres emplacements
    alt_paths = [
        "data/processed/mecha_dataset_processed.csv",
        "../data/processed/mecha_dataset_processed.csv",
        "c:/Projet/MSPR/MSPR2-MECHA/data/processed/mecha_dataset_processed.csv",
    ]
    for path in alt_paths:
        if os.path.exists(path):
            return pd.read_csv(path, parse_dates=["timestamp"])
    
    st.error("Dataset non trouve. Executez d'abord : python data/scripts/generate_data.py")
    return None


@st.cache_data(ttl=300)
def load_model_metrics():
    """Charge les metriques des modeles ML."""
    metrics_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "models", "evaluation", "model_comparison.json"
    )
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return None


# ==============================================================================
# COMPOSANTS UI
# ==============================================================================

def render_metric_card(label, value, delta=None, color_class=""):
    """Affiche une carte metrique stylisee."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_alert(message, level="info", machine=None, usine=None):
    """Affiche une alerte stylisee."""
    prefix = f"[{usine}] Machine {machine} - " if machine and usine else ""
    st.markdown(f"""
    <div class="alert-card alert-{level}">
        <strong>{prefix}{message}</strong>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# PAGES
# ==============================================================================

def page_groupe(df):
    """Vue Groupe - KPIs globaux des 5 usines (Direction generale)."""
    
    st.markdown("""
    <div class="main-header">
        <h1>Dashboard Groupe - MECHA</h1>
        <p>Vue consolidee des 5 usines | Direction Generale & Direction Industrielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs globaux
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_machines = df["machine_id"].nunique()
    machines_ok = df[df["machine_status"] == 1]["machine_id"].nunique()
    machines_panne = df[df["machine_status"] == 2]["machine_id"].nunique()
    trs_global = (machines_ok / total_machines * 100) if total_machines > 0 else 0
    taux_anomalies = df["anomaly_flag"].mean() * 100
    alertes_actives = len(df[df["anomaly_flag"] == 1]["machine_id"].unique())
    
    with col1:
        color = "success" if trs_global >= 75 else "warning" if trs_global >= 60 else "danger"
        render_metric_card("TRS Global", f"{trs_global:.1f}%", "Objectif: > 75%", color)
    with col2:
        taux_maint = df["maintenance_required"].mean() * 100
        color = "success" if taux_maint < 5 else "warning" if taux_maint < 15 else "danger"
        render_metric_card("Taux Maintenance", f"{taux_maint:.1f}%", f"{int(df['maintenance_required'].sum())} interventions", color)
    with col3:
        color = "success" if taux_anomalies < 5 else "warning" if taux_anomalies < 10 else "danger"
        render_metric_card("Anomalies", f"{taux_anomalies:.1f}%", f"Seuil: < {SEUILS['anomaly_max']}%", color)
    with col4:
        render_metric_card("Machines Actives", f"{machines_ok}/{total_machines}", f"{machines_panne} en panne")
    with col5:
        rul_moyen = df[df["machine_status"] == 1]["predicted_remaining_life"].mean()
        render_metric_card("RUL Moyen", f"{rul_moyen:.0f} min", "Duree de vie residuelle")
    
    st.markdown("---")
    
    # Graphiques
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Performance par Usine")
        usine_stats = df.groupby("usine_id").agg({
            "maintenance_required": "mean",
            "anomaly_flag": "mean",
            "temperature": "mean",
            "predicted_remaining_life": "mean",
        }).reset_index()
        usine_stats["usine_nom"] = usine_stats["usine_id"].map(USINE_NOMS)
        usine_stats["maintenance_pct"] = usine_stats["maintenance_required"] * 100
        usine_stats["anomaly_pct"] = usine_stats["anomaly_flag"] * 100
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=usine_stats["usine_nom"], 
            y=usine_stats["maintenance_pct"],
            name="Maintenance (%)",
            marker_color="#FF5252",
        ))
        fig.add_trace(go.Bar(
            x=usine_stats["usine_nom"], 
            y=usine_stats["anomaly_pct"],
            name="Anomalies (%)",
            marker_color="#FFB300",
        ))
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
        failure_counts = df[df["failure_type"] != "Normal"]["failure_type"].value_counts()
        if len(failure_counts) > 0:
            fig = px.pie(
                values=failure_counts.values,
                names=failure_counts.index,
                color_discrete_sequence=["#FF5252", "#FFB300", "#00D4FF", "#7B61FF", "#00E676"],
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
    temp_by_machine = df.groupby(["usine_id", "machine_id"])["temperature"].mean().reset_index()
    temp_by_machine["usine_nom"] = temp_by_machine["usine_id"].map(USINE_NOMS)
    
    fig = px.scatter(
        temp_by_machine,
        x="machine_id",
        y="usine_nom",
        size="temperature",
        color="temperature",
        color_continuous_scale="RdYlGn_r",
        range_color=[60, 100],
        labels={"temperature": "Temp. (C)", "machine_id": "Machine ID", "usine_nom": "Usine"},
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
    
    st.markdown("""
    <div class="main-header">
        <h1>Dashboard Site - MECHA</h1>
        <p>Vue operationnelle par usine | Directeur de site & Responsable production</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    machines_fonctionnelles = df_usine[df_usine["machine_status"] == 1]["machine_id"].nunique()
    
    with col1:
        trs = machines_fonctionnelles / machines_usine * 100 if machines_usine > 0 else 0
        color = "success" if trs >= 75 else "warning" if trs >= 60 else "danger"
        render_metric_card("TRS Site", f"{trs:.1f}%", f"{machines_fonctionnelles}/{machines_usine} machines", color)
    with col2:
        temp_moy = df_usine[df_usine["machine_status"] == 1]["temperature"].mean()
        color = "success" if temp_moy < 85 else "warning" if temp_moy < 100 else "danger"
        render_metric_card("Temp. Moyenne", f"{temp_moy:.1f} C", f"Seuil: < {SEUILS['temp_critique']}C", color)
    with col3:
        maint_pct = df_usine["maintenance_required"].mean() * 100
        render_metric_card("Maintenance Req.", f"{maint_pct:.1f}%", f"{int(df_usine['maintenance_required'].sum())} interventions")
    with col4:
        rul_min = df_usine[df_usine["machine_status"] == 1]["predicted_remaining_life"].min()
        color = "danger" if rul_min < SEUILS["rul_critique"] else "warning" if rul_min < 150 else "success"
        render_metric_card("RUL Minimum", f"{rul_min:.0f} min", "Machine la plus critique", color)
    
    st.markdown("---")
    
    # Etat des machines
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Etat des Machines")
        machine_status = df_usine.groupby("machine_id").agg({
            "temperature": "last",
            "vibration": "last",
            "predicted_remaining_life": "last",
            "machine_status": "last",
            "maintenance_required": "last",
            "machine_profile": "first",
            "downtime_risk": "last",
        }).reset_index()
        
        # Indicateur d'etat
        status_map = {0: "Arret", 1: "OK", 2: "PANNE"}
        machine_status["etat"] = machine_status["machine_status"].map(status_map)
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=["Machine", "Profil", "Etat", "Temp (C)", "Vibr.", "RUL (min)", "Risque"],
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
                    machine_status["downtime_risk"].round(2),
                ],
                fill_color=[["#1a1c2e"] * len(machine_status)],
                font=dict(color="white", size=12),
                align="center",
            ),
        )])
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
        machines_hot = df_usine[df_usine["temperature"] > SEUILS["temp_critique"]]["machine_id"].unique()
        for m in machines_hot[:5]:
            render_alert(f"Temperature critique (> {SEUILS['temp_critique']}C)", "critical", m, usine_selection)
        
        # Alertes RUL
        machines_rul = df_usine[
            (df_usine["predicted_remaining_life"] < SEUILS["rul_critique"]) & 
            (df_usine["machine_status"] == 1)
        ]["machine_id"].unique()
        for m in machines_rul[:5]:
            render_alert(f"RUL critique (< {SEUILS['rul_critique']} min)", "major", m, usine_selection)
        
        if len(machines_hot) == 0 and len(machines_rul) == 0:
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
            df_plot, x="timestamp", y="temperature",
            color="machine_id",
            labels={"temperature": "Temperature (C)", "timestamp": "Temps", "machine_id": "Machine"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.add_hline(y=SEUILS["temp_critique"], line_dash="dash", line_color="#FF5252",
                      annotation_text=f"Seuil critique ({SEUILS['temp_critique']}C)")
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
    
    st.markdown("""
    <div class="main-header">
        <h1>Vue Machine - MECHA</h1>
        <p>Diagnostic individuel | Equipe maintenance & Data team</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        machine_id = st.selectbox("Machine", sorted(df["machine_id"].unique()))
    
    df_machine = df[df["machine_id"] == machine_id]
    
    with col2:
        usine = df_machine["usine_id"].iloc[0] if len(df_machine) > 0 else "N/A"
        profile = df_machine["machine_profile"].iloc[0] if len(df_machine) > 0 else "N/A"
        st.info(f"Usine: **{USINE_NOMS.get(usine, usine)}** | Profil: **{profile}** | "
                f"Ligne: **{df_machine['ligne_production'].iloc[0]}** | "
                f"Piece: **{df_machine['type_piece'].iloc[0]}**")
    
    # KPIs machine
    col1, col2, col3, col4, col5 = st.columns(5)
    last = df_machine.iloc[-1] if len(df_machine) > 0 else {}
    
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
        risk = last.get("downtime_risk", 0)
        color = "success" if risk < 0.3 else "warning" if risk < 0.6 else "danger"
        render_metric_card("Risque Arret", f"{risk:.1%}", "", color)
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
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                           subplot_titles=("Temperature (C)", "Vibration (mm/s)", "RUL (min)"),
                           vertical_spacing=0.08)
        
        fig.add_trace(go.Scatter(x=df_machine["timestamp"], y=df_machine["temperature"],
                                 mode="lines", name="Temperature", line=dict(color="#FF5252")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_machine["timestamp"], y=df_machine["temp_rolling_10min"],
                                 mode="lines", name="Moy. Mobile 10min", line=dict(color="#FFB300", dash="dash")), row=1, col=1)
        fig.add_hline(y=SEUILS["temp_critique"], line_dash="dot", line_color="#FF5252", row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_machine["timestamp"], y=df_machine["vibration"],
                                 mode="lines", name="Vibration", line=dict(color="#00D4FF")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_machine["timestamp"], y=df_machine["vibr_rolling_10min"],
                                 mode="lines", name="Moy. Mobile 10min", line=dict(color="#7B61FF", dash="dash")), row=2, col=1)
        
        fig.add_trace(go.Scatter(x=df_machine["timestamp"], y=df_machine["predicted_remaining_life"],
                                 mode="lines", name="RUL", line=dict(color="#00E676"),
                                 fill="tozeroy", fillcolor="rgba(0,230,118,0.1)"), row=3, col=1)
        fig.add_hline(y=SEUILS["rul_critique"], line_dash="dot", line_color="#FFB300", row=3, col=1)
        
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=600, margin=dict(t=40, b=40), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("Indicateurs de Risque")
        
        # Jauge de risque
        risk_val = last.get("downtime_risk", 0)
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_val * 100,
            title={"text": "Score de Risque d'Arret (%)"},
            delta={"reference": 30},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#00D4FF"},
                "steps": [
                    {"range": [0, 30], "color": "rgba(0,230,118,0.2)"},
                    {"range": [30, 60], "color": "rgba(255,179,0,0.2)"},
                    {"range": [60, 100], "color": "rgba(255,82,82,0.2)"},
                ],
                "threshold": {"line": {"color": "#FF5252", "width": 4}, "thickness": 0.75, "value": 60},
            },
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(t=60, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Feature importance (si disponible)
        st.subheader("Facteurs de Risque")
        features = {
            "Temperature": last.get("temperature", 0) / 120,
            "Vibration": last.get("vibration", 0) / 100,
            "RUL (inverse)": 1 - last.get("predicted_remaining_life", 500) / 500,
            "Energie": last.get("energy_consumption", 0) / 7,
            "Trend Temp.": max(0, last.get("temp_trend_1h", 0) * 10),
        }
        
        fig = go.Figure(go.Bar(
            x=list(features.values()),
            y=list(features.keys()),
            orientation="h",
            marker_color=["#FF5252" if v > 0.7 else "#FFB300" if v > 0.4 else "#00E676" for v in features.values()],
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Niveau de risque normalise",
        )
        st.plotly_chart(fig, use_container_width=True)


def page_alertes(df):
    """Vue Alertes - Historique et filtre."""
    
    st.markdown("""
    <div class="main-header">
        <h1>Centre d'Alertes - MECHA</h1>
        <p>Suivi des alertes et anomalies | Tous niveaux</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        usine_filter = st.multiselect("Filtrer par usine", list(USINE_NOMS.keys()), 
                                       format_func=lambda x: USINE_NOMS[x])
    with col2:
        type_filter = st.multiselect("Type d'alerte", 
                                      ["Temperature critique", "RUL critique", "Anomalie detectee", "Panne"])
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
        alertes.append({
            "timestamp": row["timestamp"],
            "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
            "machine": row["machine_id"],
            "type": "Temperature critique",
            "niveau": "CRITIQUE",
            "detail": f"Temperature: {row['temperature']:.1f}C (seuil: {SEUILS['temp_critique']}C)",
        })
    
    # Alertes RUL
    rul_alerts = df_filtered[
        (df_filtered["predicted_remaining_life"] < SEUILS["rul_critique"]) &
        (df_filtered["machine_status"] == 1)
    ]
    for _, row in rul_alerts.head(20).iterrows():
        alertes.append({
            "timestamp": row["timestamp"],
            "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
            "machine": row["machine_id"],
            "type": "RUL critique",
            "niveau": "MAJEUR",
            "detail": f"RUL: {row['predicted_remaining_life']:.0f} min (seuil: {SEUILS['rul_critique']} min)",
        })
    
    # Alertes pannes
    panne_alerts = df_filtered[df_filtered["machine_status"] == 2]
    for _, row in panne_alerts.head(20).iterrows():
        alertes.append({
            "timestamp": row["timestamp"],
            "usine": USINE_NOMS.get(row["usine_id"], row["usine_id"]),
            "machine": row["machine_id"],
            "type": "Panne",
            "niveau": "CRITIQUE",
            "detail": f"Type: {row['failure_type']}",
        })
    
    # Afficher les alertes
    if alertes:
        df_alertes = pd.DataFrame(alertes).sort_values("timestamp", ascending=False)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            critiques = len(df_alertes[df_alertes["niveau"] == "CRITIQUE"])
            render_metric_card("Alertes Critiques", str(critiques), "", "danger" if critiques > 0 else "success")
        with col2:
            majeurs = len(df_alertes[df_alertes["niveau"] == "MAJEUR"])
            render_metric_card("Alertes Majeures", str(majeurs), "", "warning" if majeurs > 0 else "success")
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
    
    st.markdown("""
    <div class="main-header">
        <h1>Performance du Modele IA - MECHA</h1>
        <p>Suivi des metriques ML | Data team & Direction industrielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    metrics = load_model_metrics()
    
    if metrics:
        # Comparaison des modeles
        st.subheader("Comparaison des Modeles")
        models_df = pd.DataFrame(metrics).T
        st.dataframe(models_df, use_container_width=True)
    else:
        st.warning("Metriques non disponibles. Executez d'abord : python models/training/train_models.py")
        
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
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Correlation features
        feature_cols = ["temperature", "vibration", "humidity", "pressure", 
                       "energy_consumption", "predicted_remaining_life"]
        available_cols = [c for c in feature_cols if c in df.columns]
        corr = df[available_cols + ["maintenance_required"]].corr()["maintenance_required"].drop("maintenance_required")
        
        fig = go.Figure(go.Bar(
            x=corr.values,
            y=corr.index,
            orientation="h",
            marker_color=[COLORS["danger"] if abs(v) > 0.2 else COLORS["warning"] if abs(v) > 0.05 else COLORS["text_muted"] for v in corr.values],
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title="Correlation des Features avec maintenance_required",
            height=350, margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution profils machines
    st.subheader("Distribution par Profil de Machine")
    profile_stats = df.groupby("machine_profile").agg({
        "maintenance_required": "mean",
        "temperature": "mean",
        "machine_id": "nunique",
    }).reset_index()
    profile_stats["maintenance_pct"] = profile_stats["maintenance_required"] * 100
    
    fig = px.bar(
        profile_stats, x="machine_profile", y="maintenance_pct",
        color="temperature", color_continuous_scale="RdYlGn_r",
        labels={"maintenance_pct": "Taux maintenance (%)", "machine_profile": "Profil", "temperature": "Temp. moy."},
        text="machine_id",
    )
    fig.update_traces(texttemplate="%{text} machines", textposition="outside")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
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
        
        st.markdown("---")
        st.markdown("### A propos")
        st.caption("MSPR 2 - Bloc 4")
        st.caption("Equipe MECHA")
        st.caption(f"Derniere maj: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
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
