"""
MSPR 2 MECHA — Script de génération du dataset enrichi
=======================================================
Ce script génère un jeu de données simulé cohérent avec le contexte industriel
de MECHA, en enrichissant le format de base du dataset MSPR 1.

Enrichissements par rapport au dataset MSPR 1 :
- Ajout de contexte MECHA (usine, ligne de production, type de pièce)
- Features temporelles (moyenne mobile, tendance)
- Hétérogénéité entre machines (profils de fragilité)
- Séparation maintenance corrective / préventive
- Calcul de RUL réaliste avec dégradation progressive

Auteur : Équipe MECHA
Date : Mai 2026
"""

import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

# Reproductibilité
np.random.seed(42)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

NUM_MACHINES = 50
DAYS = 90  # 3 mois de données
RECORDS_PER_MACHINE_PER_DAY = 1440  # 1 par minute
START_DATE = datetime(2025, 1, 1)

# Usines MECHA (5 sites : 3 France, 2 Espagne)
USINES = {
    "USN-FR-01": {"nom": "Lyon", "pays": "France", "machines": list(range(1, 11))},
    "USN-FR-02": {"nom": "Toulouse", "pays": "France", "machines": list(range(11, 21))},
    "USN-FR-03": {"nom": "Nantes", "pays": "France", "machines": list(range(21, 31))},
    "USN-ES-01": {"nom": "Barcelone", "pays": "Espagne", "machines": list(range(31, 41))},
    "USN-ES-02": {"nom": "Madrid", "pays": "Espagne", "machines": list(range(41, 51))},
}

# Types de pièces fabriquées
TYPES_PIECES = ["Arbre_moteur", "Disque_frein", "Carter_boite", "Pale_turbine", "Axe_roue"]

# Lignes de production par usine
LIGNES_PRODUCTION = ["LP-A", "LP-B", "LP-C"]

# Profils de fragilité des machines (hétérogénéité réaliste)
MACHINE_PROFILES = {
    "robuste": {"temp_base": 70, "temp_var": 8, "vibr_base": 35, "vibr_var": 10,
                "panne_prob": 0.02, "maintenance_prev_prob": 0.05},
    "standard": {"temp_base": 75, "temp_var": 12, "vibr_base": 40, "vibr_var": 15,
                 "panne_prob": 0.04, "maintenance_prev_prob": 0.08},
    "fragile":  {"temp_base": 82, "temp_var": 15, "vibr_base": 50, "vibr_var": 20,
                 "panne_prob": 0.08, "maintenance_prev_prob": 0.12},
    "vieillissante": {"temp_base": 85, "temp_var": 18, "vibr_base": 55, "vibr_var": 25,
                      "panne_prob": 0.10, "maintenance_prev_prob": 0.15},
}


def assign_machine_profile(machine_id: int) -> str:
    """Assigne un profil de fragilité à chaque machine (hétérogénéité réaliste)."""
    if machine_id in [5, 12, 24, 37, 43]:
        return "vieillissante"
    elif machine_id in [3, 8, 15, 22, 32, 41, 48]:
        return "fragile"
    elif machine_id in [1, 10, 20, 30, 40, 50]:
        return "robuste"
    else:
        return "standard"


def get_usine_for_machine(machine_id: int) -> tuple:
    """Retourne (usine_id, nom_usine, pays) pour une machine."""
    for usine_id, info in USINES.items():
        if machine_id in info["machines"]:
            return usine_id, info["nom"], info["pays"]
    return "USN-FR-01", "Lyon", "France"


def generate_machine_data(machine_id: int, num_records: int) -> pd.DataFrame:
    """
    Génère les données pour une machine avec dégradation progressive et pannes.
    
    La logique simule un comportement industriel réaliste :
    1. La machine fonctionne normalement avec du bruit capteur
    2. Des épisodes de dégradation progressive surviennent
    3. La dégradation augmente la température et les vibrations
    4. Au-delà de certains seuils, une panne se déclenche
    5. Après maintenance, les paramètres reviennent à la normale
    """
    profile_name = assign_machine_profile(machine_id)
    profile = MACHINE_PROFILES[profile_name]
    usine_id, usine_nom, usine_pays = get_usine_for_machine(machine_id)
    
    # Timestamps
    timestamps = [START_DATE + timedelta(minutes=i) for i in range(num_records)]
    
    # Initialisation
    temperature = np.zeros(num_records)
    vibration = np.zeros(num_records)
    humidity = np.zeros(num_records)
    pressure = np.zeros(num_records)
    energy_consumption = np.zeros(num_records)
    machine_status = np.zeros(num_records, dtype=int)  # 0=Arrêt, 1=Fonct, 2=Panne
    anomaly_flag = np.zeros(num_records, dtype=int)
    failure_type = ["Normal"] * num_records
    maintenance_required = np.zeros(num_records, dtype=int)
    maintenance_type = ["none"] * num_records
    rul = np.zeros(num_records)
    
    # État de dégradation
    degradation = 0.0
    time_since_maintenance = 0
    max_rul = 500  # RUL max en minutes
    in_failure = False
    failure_countdown = 0
    
    for i in range(num_records):
        # Cycle journalier (arrêt la nuit)
        hour = timestamps[i].hour
        is_production = 6 <= hour <= 22  # Production de 6h à 22h
        
        if not is_production:
            machine_status[i] = 0  # Arrêt planifié
            temperature[i] = profile["temp_base"] * 0.4 + np.random.normal(0, 2)
            vibration[i] = max(0, np.random.normal(5, 2))
            humidity[i] = np.random.uniform(40, 70)
            pressure[i] = np.random.uniform(1.0, 2.0)
            energy_consumption[i] = np.random.uniform(0.3, 0.8)
            rul[i] = max_rul - degradation * max_rul
            continue
        
        # Gestion de la panne en cours
        if in_failure:
            failure_countdown -= 1
            machine_status[i] = 2  # Panne
            temperature[i] = profile["temp_base"] + 30 + np.random.normal(0, 5)
            vibration[i] = max(0, profile["vibr_base"] + 40 + np.random.normal(0, 10))
            humidity[i] = np.random.uniform(30, 80)
            pressure[i] = np.random.uniform(0.5, 2.0)
            energy_consumption[i] = np.random.uniform(0.1, 1.0)
            anomaly_flag[i] = 1
            maintenance_required[i] = 1
            maintenance_type[i] = "corrective"
            rul[i] = 0
            
            if failure_countdown <= 0:
                # Maintenance corrective terminée — reset
                in_failure = False
                degradation = 0.0
                time_since_maintenance = 0
            continue
        
        # Dégradation progressive
        time_since_maintenance += 1
        degradation_rate = profile["panne_prob"] * 0.01
        degradation = min(1.0, degradation + degradation_rate + np.random.normal(0, 0.005))
        
        # Température = base + dégradation + bruit
        temp_degradation = degradation * 40  # Jusqu'à +40°C de surchauffe
        temperature[i] = (profile["temp_base"] + temp_degradation + 
                         np.random.normal(0, profile["temp_var"] * 0.3))
        
        # Vibration = base + dégradation + bruit
        vibr_degradation = degradation * 30
        vibration[i] = max(0, profile["vibr_base"] + vibr_degradation + 
                          np.random.normal(0, profile["vibr_var"] * 0.3))
        
        # Capteurs environnementaux (peu corrélés à la maintenance)
        humidity[i] = np.random.uniform(30, 80)
        pressure[i] = np.random.uniform(1.0, 5.0)
        energy_consumption[i] = (2.5 + degradation * 2.0 + 
                                np.random.normal(0, 0.5))
        energy_consumption[i] = np.clip(energy_consumption[i], 0.5, 7.0)
        
        # RUL (Remaining Useful Life)
        rul[i] = max(0, max_rul * (1 - degradation))
        
        # Machine en fonctionnement normal
        machine_status[i] = 1
        
        # Détection d'anomalie
        if temperature[i] > 100 or vibration[i] > 70 or degradation > 0.7:
            anomaly_flag[i] = 1
        
        # Déterminer le type de panne
        if temperature[i] > 110:
            failure_type[i] = "Overheating"
        elif vibration[i] > 80:
            failure_type[i] = "Vibration_Issue"
        elif pressure[i] < 1.2 and degradation > 0.5:
            failure_type[i] = "Pressure_Drop"
        elif energy_consumption[i] > 6.0:
            failure_type[i] = "Electrical_Fault"
        
        # Déclenchement de panne
        if degradation > 0.85 and np.random.random() < profile["panne_prob"]:
            in_failure = True
            failure_countdown = np.random.randint(30, 120)  # 30 min à 2h de réparation
            machine_status[i] = 2
            maintenance_required[i] = 1
            maintenance_type[i] = "corrective"
            rul[i] = 0
            if failure_type[i] == "Normal":
                failure_type[i] = np.random.choice(
                    ["Overheating", "Vibration_Issue", "Pressure_Drop", "Electrical_Fault"],
                    p=[0.35, 0.30, 0.20, 0.15]
                )
            continue
        
        # Maintenance préventive (planifiée)
        if (time_since_maintenance > 200 and  # Au moins ~3h de fonctionnement
            degradation > 0.4 and 
            np.random.random() < profile["maintenance_prev_prob"] * 0.05):
            maintenance_required[i] = 1
            maintenance_type[i] = "preventive"
            # Après maintenance préventive, la dégradation diminue
            degradation *= 0.3
            time_since_maintenance = 0
        
        # Maintenance requise si dégradation élevée
        if degradation > 0.6:
            maintenance_required[i] = 1
            if maintenance_type[i] == "none":
                maintenance_type[i] = "recommended"
    
    # Construire le DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "machine_id": machine_id,
        "usine_id": usine_id,
        "usine_nom": usine_nom,
        "usine_pays": usine_pays,
        "ligne_production": np.random.choice(LIGNES_PRODUCTION),
        "type_piece": np.random.choice(TYPES_PIECES),
        "machine_profile": profile_name,
        "temperature": np.round(temperature, 2),
        "vibration": np.round(vibration, 2),
        "humidity": np.round(humidity, 2),
        "pressure": np.round(pressure, 2),
        "energy_consumption": np.round(energy_consumption, 2),
        "machine_status": machine_status,
        "anomaly_flag": anomaly_flag,
        "predicted_remaining_life": np.round(rul, 0).astype(int),
        "failure_type": failure_type,
        "maintenance_required": maintenance_required,
        "maintenance_type": maintenance_type,
    })
    
    return df


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les features temporelles glissantes (recommandation MSPR 1).
    - Moyenne mobile température (10 min)
    - Tendance température (1h)  
    - Moyenne mobile vibration (10 min)
    - Écart-type température (30 min)
    """
    print("  Ajout des features temporelles...")
    
    # Trier par machine et timestamp
    df = df.sort_values(["machine_id", "timestamp"]).reset_index(drop=True)
    
    # Features par machine
    for machine_id in df["machine_id"].unique():
        mask = df["machine_id"] == machine_id
        
        # Moyenne mobile température (10 min)
        df.loc[mask, "temp_rolling_10min"] = (
            df.loc[mask, "temperature"].rolling(window=10, min_periods=1).mean()
        )
        
        # Tendance température (60 min) — pente linéaire
        df.loc[mask, "temp_trend_1h"] = (
            df.loc[mask, "temperature"].rolling(window=60, min_periods=1)
            .apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0, raw=False)
        )
        
        # Moyenne mobile vibration (10 min)
        df.loc[mask, "vibr_rolling_10min"] = (
            df.loc[mask, "vibration"].rolling(window=10, min_periods=1).mean()
        )
        
        # Écart-type température (30 min) — indicateur de stabilité
        df.loc[mask, "temp_std_30min"] = (
            df.loc[mask, "temperature"].rolling(window=30, min_periods=1).std().fillna(0)
        )
        
        # Ratio énergie / vibration (indicateur d'efficacité)
        vibr_safe = df.loc[mask, "vibration"].replace(0, 0.01)
        df.loc[mask, "energy_vibr_ratio"] = (
            df.loc[mask, "energy_consumption"] / vibr_safe
        )
    
    # Arrondir
    for col in ["temp_rolling_10min", "temp_trend_1h", "vibr_rolling_10min", 
                "temp_std_30min", "energy_vibr_ratio"]:
        df[col] = df[col].round(4)
    
    return df


def compute_downtime_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule un score de risque d'arrêt basé sur les capteurs."""
    risk = np.zeros(len(df))
    
    # Composantes du risque
    temp_risk = np.clip((df["temperature"] - 80) / 40, 0, 1)  # > 80°C = risque
    vibr_risk = np.clip((df["vibration"] - 50) / 40, 0, 1)    # > 50 = risque
    rul_risk = np.clip(1 - df["predicted_remaining_life"] / 500, 0, 1)
    
    # Score composite
    risk = 0.3 * temp_risk + 0.25 * vibr_risk + 0.45 * rul_risk
    df["downtime_risk"] = np.round(risk, 4)
    
    return df


def generate_full_dataset():
    """Génère le dataset complet enrichi pour MECHA."""
    print("=" * 60)
    print("MECHA — Génération du dataset enrichi MSPR 2")
    print("=" * 60)
    
    # Limiter pour la performance (échantillonner 2000 records par machine ≈ 100k total)
    records_per_machine = 2000
    
    all_data = []
    for machine_id in range(1, NUM_MACHINES + 1):
        profile = assign_machine_profile(machine_id)
        usine_id, usine_nom, _ = get_usine_for_machine(machine_id)
        print(f"  Machine {machine_id:02d}/{NUM_MACHINES} "
              f"({profile:15s}) — {usine_id} ({usine_nom})")
        
        # Générer plus de données puis échantillonner
        full_records = RECORDS_PER_MACHINE_PER_DAY * 3  # 3 jours complets
        df_machine = generate_machine_data(machine_id, full_records)
        
        # Échantillonner uniformément
        if len(df_machine) > records_per_machine:
            indices = np.linspace(0, len(df_machine) - 1, records_per_machine, dtype=int)
            df_machine = df_machine.iloc[indices].reset_index(drop=True)
        
        all_data.append(df_machine)
    
    print(f"\n  Fusion des données ({NUM_MACHINES} machines)...")
    df = pd.concat(all_data, ignore_index=True)
    
    # Ajouter les features temporelles
    df = add_temporal_features(df)
    
    # Calculer le risque d'arrêt
    df = compute_downtime_risk(df)
    
    # Statistiques
    print(f"\n{'=' * 60}")
    print(f"  STATISTIQUES DU DATASET GÉNÉRÉ")
    print(f"{'=' * 60}")
    print(f"  Total enregistrements : {len(df):,}")
    print(f"  Colonnes             : {len(df.columns)}")
    print(f"  Machines             : {df['machine_id'].nunique()}")
    print(f"  Usines               : {df['usine_id'].nunique()}")
    print(f"  Plage temporelle     : {df['timestamp'].min()} -> {df['timestamp'].max()}")
    print(f"\n  Distribution maintenance_required :")
    print(f"    0 (pas de maintenance) : {(df['maintenance_required'] == 0).sum():,} "
          f"({(df['maintenance_required'] == 0).mean():.1%})")
    print(f"    1 (maintenance requise): {(df['maintenance_required'] == 1).sum():,} "
          f"({(df['maintenance_required'] == 1).mean():.1%})")
    print(f"\n  Distribution machine_status :")
    for status, label in [(0, "Arrêt"), (1, "Fonctionnement"), (2, "Panne")]:
        count = (df["machine_status"] == status).sum()
        print(f"    {status} ({label:15s}) : {count:,} ({count/len(df):.1%})")
    print(f"\n  Distribution maintenance_type :")
    for mt in df["maintenance_type"].unique():
        count = (df["maintenance_type"] == mt).sum()
        print(f"    {mt:15s} : {count:,} ({count/len(df):.1%})")
    print(f"\n  Profils machines :")
    for profile in df["machine_profile"].unique():
        count = df[df["machine_profile"] == profile]["machine_id"].nunique()
        print(f"    {profile:15s} : {count} machines")
    
    # Sauvegarder
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raw")
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, "mecha_dataset_raw.csv")
    df.to_csv(raw_path, index=False)
    print(f"\n  [OK] Dataset brut sauvegarde : {raw_path}")
    print(f"     Taille : {os.path.getsize(raw_path) / 1024 / 1024:.1f} Mo")
    
    # Version processed (sans les timestamps pour le ML)
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "processed")
    os.makedirs(processed_dir, exist_ok=True)
    processed_path = os.path.join(processed_dir, "mecha_dataset_processed.csv")
    df.to_csv(processed_path, index=False)
    print(f"  [OK] Dataset traite sauvegarde : {processed_path}")
    
    return df


if __name__ == "__main__":
    df = generate_full_dataset()
    print(f"\n{'=' * 60}")
    print("  GÉNÉRATION TERMINÉE AVEC SUCCÈS")
    print(f"{'=' * 60}")
