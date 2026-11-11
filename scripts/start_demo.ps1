param(
    [switch]$Local,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -Path $RepoRoot

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  MECHA Predict (MSPR TPRE841) — Lancement Demo Soutenance" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

# 1. Creer .env automatiquement si absent
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Fichier .env cree automatiquement depuis .env.example" -ForegroundColor Green
}

# 2. Detecter Docker Desktop si -Local n'est pas force
$UseDocker = $false
if (-not $Local) {
    try {
        $null = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            $UseDocker = $true
        }
    } catch {
        $UseDocker = $false
    }
    if (-not $UseDocker) {
        Write-Host "[INFO] Docker Desktop non detecte ou arrete -> Bascule automatique en mode Python local !" -ForegroundColor Yellow
    }
}

if ($UseDocker) {
    Write-Host "`n[MODE DOCKER COMPLET] PostgreSQL 15 + FastAPI + Streamlit (6 vues) + Grafana" -ForegroundColor Green
    Write-Host "Construction et demarrage des conteneurs (le 1er lancement genere les 110 000 lignes et entraine les 5 modeles ML)..." -ForegroundColor Gray

    # S'assurer que db/load_data.sh est bien en LF meme sur un ZIP / clone Windows
    if (Test-Path "db\load_data.sh") {
        $shContent = [System.IO.File]::ReadAllText((Resolve-Path "db\load_data.sh"))
        if ($shContent.Contains("`r`n")) {
            [System.IO.File]::WriteAllText((Resolve-Path "db\load_data.sh"), $shContent.Replace("`r`n", "`n"))
        }
    }

    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) {
        throw "Echec de 'docker compose up --build -d'."
    }

    # Verifier que PostgreSQL contient bien les 110 000 lignes (cas d'un ancien volume vide)
    Write-Host "Verification des donnees PostgreSQL..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    $rowCount = (docker exec mecha-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT COUNT(*) FROM mecha_data;"' 2>$null)
    if ($rowCount -match "^\d+$" -and [int]$rowCount -eq 0) {
        Write-Host "[INFO] Volume PostgreSQL vide detecte -> Chargement des 110 000 lignes..." -ForegroundColor Yellow
        docker exec mecha-db bash /docker-entrypoint-initdb.d/99-load-data.sh
    }

    # Attendre que l'API et Streamlit repondent
    Write-Host "Attente de disponibilite de l'API IA et du Dashboard Streamlit..." -ForegroundColor Gray
    for ($i = 1; $i -le 30; $i++) {
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
            if ($resp.status -eq "healthy") { break }
        } catch {}
        Start-Sleep -Seconds 2
    }

    Write-Host "`n==============================================================" -ForegroundColor Green
    Write-Host "  DEMO DOCKER PRETE !" -ForegroundColor Green
    Write-Host "  - Dashboard Metier Streamlit (6 vues) : http://localhost:8501"
    Write-Host "  - API IA FastAPI (Swagger /docs)      : http://localhost:8000/docs"
    Write-Host "  - Supervision Grafana (admin/changeme): http://localhost:3000"
    Write-Host "  (Pour tout arreter apres la soutenance : scripts\stop_demo.bat)" -ForegroundColor Gray
    Write-Host "==============================================================" -ForegroundColor Green

    if (-not $NoBrowser) {
        Start-Process "http://localhost:8501"
        Start-Process "http://localhost:8000/docs"
        Start-Process "http://localhost:3000"
    }
}
else {
    Write-Host "`n[MODE PYTHON LOCAL SANS DOCKER] FastAPI + Streamlit (6 vues)" -ForegroundColor Green

    # Trouver Python 3.11+
    $PyCmd = "python"
    if (-not (Get-Command $PyCmd -ErrorAction SilentlyContinue)) {
        $PyCmd = "py"
    }

    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "[1/4] Creation de l'environnement virtuel .venv..." -ForegroundColor Gray
        & $PyCmd -m venv .venv
    }
    $VenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"

    Write-Host "[2/4] Verification des dependances Python..." -ForegroundColor Gray
    & $VenvPy -m pip install --quiet --upgrade pip
    & $VenvPy -m pip install --quiet -r requirements.txt -r app\requirements.txt

    if (-not (Test-Path "data\processed\mecha_dataset_processed.csv")) {
        Write-Host "[3/4] Generation du dataset hybride (110 000 lignes)..." -ForegroundColor Gray
        & $VenvPy data\scripts\generate_data.py
        & $VenvPy data\scripts\merge_datasets.py
    } else {
        Write-Host "[3/4] Dataset deja present (110 000 lignes)." -ForegroundColor Gray
    }

    if (-not (Test-Path "models\saved_models\random_forest_classifier.joblib")) {
        Write-Host "[4/4] Entrainement des 5 modeles ML..." -ForegroundColor Gray
        & $VenvPy models\training\train_models.py
    } else {
        Write-Host "[4/4] Modeles ML deja entraines." -ForegroundColor Gray
    }

    $env:MODEL_PATH = Join-Path $RepoRoot "models\saved_models"
    $env:API_URL = "http://localhost:8000"

    Write-Host "Demarrage de FastAPI (port 8000) et Streamlit (port 8501)..." -ForegroundColor Gray
    Start-Process -FilePath $VenvPy -WorkingDirectory $RepoRoot -ArgumentList "-m uvicorn api.main:app --host 127.0.0.1 --port 8000" -WindowStyle Minimized
    Start-Sleep -Seconds 3
    Start-Process -FilePath $VenvPy -WorkingDirectory $RepoRoot -ArgumentList "-m streamlit run app\src\dashboard.py --server.port 8501 --server.headless true --theme.base dark" -WindowStyle Minimized
    Start-Sleep -Seconds 3

    Write-Host "`n==============================================================" -ForegroundColor Green
    Write-Host "  DEMO LOCALE PRETE !" -ForegroundColor Green
    Write-Host "  - Dashboard Metier Streamlit (6 vues) : http://localhost:8501"
    Write-Host "  - API IA FastAPI (Swagger /docs)      : http://localhost:8000/docs"
    Write-Host "  (Pour tout arreter apres la soutenance : scripts\stop_demo.bat)" -ForegroundColor Gray
    Write-Host "==============================================================" -ForegroundColor Green

    if (-not $NoBrowser) {
        Start-Process "http://localhost:8501"
        Start-Process "http://localhost:8000/docs"
    }
}
