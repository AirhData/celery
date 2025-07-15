#!/bin/bash

echo "=== DIAGNOSTIC COMPLET ==="
echo "Date: $(date)"
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Port: ${PORT:-8000}"

# Vérifier les fichiers
echo "=== VÉRIFICATION FICHIERS ==="
ls -la
echo "Contenu tasks/:"
ls -la tasks/ 2>/dev/null || echo "Dossier tasks/ introuvable"

# Vérifier les variables d'environnement
echo "=== VARIABLES D'ENVIRONNEMENT ==="
echo "UPSTASH_REDIS_URL: ${UPSTASH_REDIS_URL:+SET}"
echo "UPSTASH_REDIS_TOKEN: ${UPSTASH_REDIS_TOKEN:+SET}"
echo "PYTHONPATH: $PYTHONPATH"

# Tester les imports Python
echo "=== TEST IMPORTS PYTHON ==="
python -c "
try:
    print('✅ Imports de base...')
    import fastapi
    import celery
    import upstash_redis
    import dotenv
    print('✅ Imports FastAPI/Celery OK')
    
    print('✅ Test import main.py...')
    import main
    print('✅ main.py OK')
    
    print('✅ Test import worker...')
    from tasks.worker_celery import celery_app
    print('✅ worker_celery OK')
    
except Exception as e:
    print(f'❌ ERREUR IMPORT: {e}')
    import traceback
    traceback.print_exc()
"

# Test connexion Redis
echo "=== TEST CONNEXION REDIS ==="
python -c "
try:
    import os
    from upstash_redis import Redis
    
    redis_url = os.environ.get('UPSTASH_REDIS_URL')
    redis_token = os.environ.get('UPSTASH_REDIS_TOKEN')
    
    if not redis_url or not redis_token:
        print('❌ Variables Redis manquantes')
    else:
        print('✅ Variables Redis présentes')
        # Test connexion basique
        redis = Redis(url=redis_url, token=redis_token)
        redis.ping()
        print('✅ Connexion Redis OK')
        
except Exception as e:
    print(f'❌ ERREUR REDIS: {e}')
"

# Démarrage simplifié API seulement
echo "=== DÉMARRAGE API SEULEMENT ==="
echo "Tentative de démarrage FastAPI..."
exec python -c "
import uvicorn
from main import app
print('Démarrage uvicorn...')
uvicorn.run(app, host='0.0.0.0', port=${PORT:-8000}, log_level='debug')
"
