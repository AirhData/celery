FROM python:3.11-slim

WORKDIR /app

# Variables d'environnement
ENV PYTHONPATH=/app
ENV HF_HOME=/app/cache
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Créer les répertoires nécessaires
RUN mkdir -p /app/cache

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port (Render gère automatiquement)
EXPOSE 8000

# Script inline pour démarrer Celery + API
CMD sh -c "python -m celery -A tasks.worker_celery:celery_app worker --loglevel=info & python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
