# ==============================================================================
# MSPR 2 MECHA -- Dockerfile API FastAPI
# ==============================================================================
# Build optimise : couche deps separee pour cache Docker maximal
# ==============================================================================

FROM python:3.11-slim AS base

# Metadonnees
LABEL maintainer="Equipe MECHA - EPSI RNCP35584"
LABEL description="API de maintenance predictive industrielle MECHA"

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Repertoire de travail
WORKDIR /app

# --- Stage 1 : Installation des dependances ---
FROM base AS dependencies

# Installer les dependances systeme necessaires (build tools pour certaines libs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2 : Image finale allegee ---
FROM base AS runtime

# Copier les packages Python installes depuis le stage dependencies
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Creer un utilisateur non-root pour la securite
RUN groupadd --gid 1000 mecha && \
    useradd --uid 1000 --gid mecha --shell /bin/bash --create-home mecha

# Copier le code applicatif
COPY . /app/api/

# Creer le repertoire pour les modeles (sera monte en volume)
RUN mkdir -p /app/models/saved_models && \
    chown -R mecha:mecha /app

# Basculer sur l'utilisateur non-root
USER mecha

# Port expose
EXPOSE 8000

# Healthcheck integre
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Commande de demarrage
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
