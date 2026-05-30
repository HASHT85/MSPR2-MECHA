-- =============================================================================
-- MECHA - Script d'initialisation PostgreSQL
-- Cree la table principale et charge les donnees de reference
-- =============================================================================

-- Table principale des donnees capteurs
CREATE TABLE IF NOT EXISTS mecha_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    machine_id INTEGER NOT NULL,
    usine_id VARCHAR(20) NOT NULL,
    usine_nom VARCHAR(50),
    usine_pays VARCHAR(20),
    ligne_production VARCHAR(10),
    type_piece VARCHAR(50),
    machine_profile VARCHAR(20),
    temperature FLOAT,
    vibration FLOAT,
    humidity FLOAT,
    pressure FLOAT,
    energy_consumption FLOAT,
    machine_status INTEGER DEFAULT 1,
    anomaly_flag INTEGER DEFAULT 0,
    predicted_remaining_life INTEGER,
    failure_type VARCHAR(30) DEFAULT 'Normal',
    maintenance_required INTEGER DEFAULT 0,
    maintenance_type VARCHAR(20) DEFAULT 'none',
    torque_nm FLOAT,
    rotational_speed_rpm INTEGER,
    tool_wear_min INTEGER,
    product_quality VARCHAR(5),
    data_source VARCHAR(30),
    temp_rolling_10min FLOAT,
    temp_trend_1h FLOAT,
    vibr_rolling_10min FLOAT,
    temp_std_30min FLOAT,
    energy_vibr_ratio FLOAT,
    downtime_risk FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les requetes frequentes
CREATE INDEX IF NOT EXISTS idx_mecha_timestamp ON mecha_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_mecha_machine ON mecha_data(machine_id);
CREATE INDEX IF NOT EXISTS idx_mecha_usine ON mecha_data(usine_id);
CREATE INDEX IF NOT EXISTS idx_mecha_maintenance ON mecha_data(maintenance_required);
CREATE INDEX IF NOT EXISTS idx_mecha_status ON mecha_data(machine_status);
CREATE INDEX IF NOT EXISTS idx_mecha_source ON mecha_data(data_source);

-- Table des alertes
CREATE TABLE IF NOT EXISTS mecha_alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    machine_id INTEGER NOT NULL,
    usine_id VARCHAR(20),
    alert_type VARCHAR(30) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_alerts_machine ON mecha_alerts(machine_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON mecha_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON mecha_alerts(resolved);

-- Table des predictions ML
CREATE TABLE IF NOT EXISTS mecha_predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    machine_id INTEGER NOT NULL,
    model_used VARCHAR(30) NOT NULL,
    prediction INTEGER,
    confidence FLOAT,
    rul_hours FLOAT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    features_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_predictions_machine ON mecha_predictions(machine_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON mecha_predictions(model_used);

-- Vue pour le dashboard Grafana
CREATE OR REPLACE VIEW v_machine_status AS
SELECT DISTINCT ON (m.machine_id)
    m.machine_id,
    m.usine_id,
    m.usine_nom,
    m.machine_profile,
    m.temperature,
    m.vibration,
    m.predicted_remaining_life,
    m.maintenance_required,
    m.machine_status,
    m.anomaly_flag,
    m.failure_type,
    m.downtime_risk,
    m.data_source,
    m.timestamp
FROM mecha_data m
ORDER BY m.machine_id, m.timestamp DESC;

-- Donnees de reference : usines
CREATE TABLE IF NOT EXISTS mecha_usines (
    usine_id VARCHAR(20) PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    pays VARCHAR(20) NOT NULL,
    ville VARCHAR(50),
    nb_machines INTEGER DEFAULT 10,
    date_ouverture DATE
);

INSERT INTO mecha_usines (usine_id, nom, pays, ville, nb_machines, date_ouverture) VALUES
    ('USN-FR-01', 'MECHA Lyon', 'France', 'Lyon', 10, '2018-03-15'),
    ('USN-FR-02', 'MECHA Toulouse', 'France', 'Toulouse', 10, '2019-06-01'),
    ('USN-FR-03', 'MECHA Nantes', 'France', 'Nantes', 10, '2021-01-10'),
    ('USN-ES-01', 'MECHA Barcelone', 'Espagne', 'Barcelone', 10, '2022-09-20'),
    ('USN-ES-02', 'MECHA Madrid', 'Espagne', 'Madrid', 10, '2023-04-05')
ON CONFLICT (usine_id) DO NOTHING;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO mecha_user;
