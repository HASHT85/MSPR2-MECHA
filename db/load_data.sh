#!/bin/bash
# =============================================================================
# MECHA - Auto data ingestion script
# Loads mecha_dataset_processed.csv into PostgreSQL on first startup
# =============================================================================

set -e

echo "=== MECHA Data Loader ==="

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready."

# Check if mecha_data table already has data
ROW_COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT COUNT(*) FROM mecha_data;")

if [ "$ROW_COUNT" -gt 0 ]; then
  echo "mecha_data already contains $ROW_COUNT rows. Skipping import."
  exit 0
fi

CSV_FILE="/docker-entrypoint-initdb.d/mecha_dataset_processed.csv"

if [ ! -f "$CSV_FILE" ]; then
  echo "WARNING: CSV file not found at $CSV_FILE. Skipping import."
  exit 0
fi

echo "Importing data from $CSV_FILE ..."

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\COPY mecha_data(timestamp, machine_id, usine_id, usine_nom, usine_pays, ligne_production, type_piece, machine_profile, temperature, vibration, humidity, pressure, energy_consumption, machine_status, anomaly_flag, predicted_remaining_life, failure_type, maintenance_required, maintenance_type, temp_rolling_10min, temp_trend_1h, vibr_rolling_10min, temp_std_30min, energy_vibr_ratio, downtime_risk, data_source, torque_nm, rotational_speed_rpm, tool_wear_min, product_quality) FROM '$CSV_FILE' WITH (FORMAT csv, HEADER true);"

NEW_COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT COUNT(*) FROM mecha_data;")
echo "Import complete. $NEW_COUNT rows loaded."

# Recreate v_machine_status view (column types may change from INTEGER to FLOAT after COPY)
echo "Recreating v_machine_status view..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
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
"

echo "=== MECHA Data Loader complete ==="
