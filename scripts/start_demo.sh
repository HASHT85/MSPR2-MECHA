#!/usr/bin/env bash
# ==============================================================================
# MECHA Predict (MSPR TPRE841) — Lancement Demo Soutenance (macOS / Linux)
# Usage :
#   ./scripts/start_demo.sh           # Mode Docker complet (bascule Python si Docker absent)
#   ./scripts/start_demo.sh --local   # Force le mode Python local sans Docker
# ==============================================================================

set -euo pipefail
cd "$(dirname "$0")/.."

LOCAL_MODE=false
OPEN_BROWSER=true
for arg in "$@"; do
  case "$arg" in
    --local) LOCAL_MODE=true ;;
    --no-browser) OPEN_BROWSER=false ;;
  esac
done

open_url() {
  if [ "$OPEN_BROWSER" = true ]; then
    if command -v open >/dev/null 2>&1; then
      open "$1" >/dev/null 2>&1 || true
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$1" >/dev/null 2>&1 || true
    fi
  fi
}

echo "=============================================================="
echo "  MECHA Predict (MSPR TPRE841) — Lancement Demo Soutenance"
echo "=============================================================="

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[OK] Fichier .env cree automatiquement depuis .env.example"
fi

USE_DOCKER=false
if [ "$LOCAL_MODE" = false ]; then
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    USE_DOCKER=true
  else
    echo "[INFO] Docker non detecte ou arrete -> Bascule automatique en mode Python local !"
  fi
fi

if [ "$USE_DOCKER" = true ]; then
  echo ""
  echo "[MODE DOCKER COMPLET] PostgreSQL 15 + FastAPI + Streamlit (6 vues) + Grafana"
  docker compose up --build -d

  echo "Verification des donnees PostgreSQL..."
  sleep 3
  ROW_COUNT=$(docker exec mecha-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT COUNT(*) FROM mecha_data;"' 2>/dev/null || echo "0")
  if [ "${ROW_COUNT:-0}" = "0" ]; then
    echo "[INFO] Volume PostgreSQL vide detecte -> Chargement des 110 000 lignes..."
    docker exec mecha-db bash /docker-entrypoint-initdb.d/99-load-data.sh
  fi

  echo "Attente de disponibilite de l'API IA..."
  for _ in $(seq 1 30); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  echo ""
  echo "=============================================================="
  echo "  DEMO DOCKER PRETE !"
  echo "  - Dashboard Metier Streamlit (6 vues) : http://localhost:8501"
  echo "  - API IA FastAPI (Swagger /docs)      : http://localhost:8000/docs"
  echo "  - Supervision Grafana (admin/changeme): http://localhost:3000"
  echo "  (Pour tout arreter : ./scripts/stop_demo.sh)"
  echo "=============================================================="

  open_url "http://localhost:8501"
  open_url "http://localhost:8000/docs"
  open_url "http://localhost:3000"
else
  echo ""
  echo "[MODE PYTHON LOCAL SANS DOCKER] FastAPI + Streamlit (6 vues)"

  if [ ! -x ".venv/bin/python" ]; then
    echo "[1/4] Creation de l'environnement virtuel .venv..."
    python3 -m venv .venv
  fi

  echo "[2/4] Verification des dependances Python..."
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements.txt -r app/requirements.txt

  if [ ! -f "data/processed/mecha_dataset_processed.csv" ]; then
    echo "[3/4] Generation du dataset hybride (110 000 lignes)..."
    .venv/bin/python data/scripts/generate_data.py
    .venv/bin/python data/scripts/merge_datasets.py
  else
    echo "[3/4] Dataset deja present (110 000 lignes)."
  fi

  if [ ! -f "models/saved_models/random_forest_classifier.joblib" ]; then
    echo "[4/4] Entrainement des 5 modeles ML..."
    .venv/bin/python models/training/train_models.py
  else
    echo "[4/4] Modeles ML deja entraines."
  fi

  export MODEL_PATH="$(pwd)/models/saved_models"
  export API_URL="http://localhost:8000"

  nohup .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 > /tmp/mecha_api.log 2>&1 &
  sleep 2
  nohup .venv/bin/streamlit run app/src/dashboard.py --server.port 8501 --server.headless true --theme.base dark > /tmp/mecha_streamlit.log 2>&1 &
  sleep 3

  echo ""
  echo "=============================================================="
  echo "  DEMO LOCALE PRETE !"
  echo "  - Dashboard Metier Streamlit (6 vues) : http://localhost:8501"
  echo "  - API IA FastAPI (Swagger /docs)      : http://localhost:8000/docs"
  echo "  (Pour tout arreter : ./scripts/stop_demo.sh)"
  echo "=============================================================="

  open_url "http://localhost:8501"
  open_url "http://localhost:8000/docs"
fi
