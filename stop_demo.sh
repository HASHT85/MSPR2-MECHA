#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Arret des conteneurs Docker MECHA (si actifs)..."
docker compose down >/dev/null 2>&1 || true

echo "Arret des processus Python locaux FastAPI / Streamlit (si actifs)..."
pkill -f "uvicorn api.main:app" >/dev/null 2>&1 || true
pkill -f "streamlit run app/src/dashboard.py" >/dev/null 2>&1 || true

echo "[OK] Demo MECHA arretee proprement."
