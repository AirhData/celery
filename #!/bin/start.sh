#!/bin/bash
# Lancer le worker Celery en arrière-plan
echo "Lancement du worker Celery..."
python -m celery -A tasks.worker_celery:celery_app worker --loglevel=info &
# Lancer l'API FastAPI au premier plan
echo "Lancement de l'API sur le port 8000..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
