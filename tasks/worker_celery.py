import os
import json
import requests
from celery import Celery
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# URL de votre API ML principale (pour les callbacks si nécessaire)
ML_API_BASE_URL = os.environ.get("ML_API_BASE_URL", "https://votre-api-ml.onrender.com")

# --- Configuration de Celery avec Upstash ---
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")

if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    raise ValueError("Les variables d'environnement UPSTASH_REDIS_URL et UPSTASH_REDIS_TOKEN sont requises.")

# Formatage de l'URL pour Celery avec SSL
# Format: rediss://:<token>@<host>:<port>/<db>
redis_host = UPSTASH_REDIS_URL.replace('https://', '').replace('http://', '')
broker_url = f"rediss://:{UPSTASH_REDIS_TOKEN}@{redis_host}"

print(f"Configuration Redis: {redis_host}")

celery_app = Celery(
    'worker_celery',
    broker=broker_url,
    backend=broker_url,
    broker_connection_retry_on_startup=True
)

# Configuration Celery optimisée pour Upstash
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Configuration SSL pour Upstash
    broker_use_ssl={
        'ssl_cert_reqs': 'none',
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': 'none',
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
    },
    
    # Gestion des erreurs
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Retry settings
    task_routes={
        'tasks.run_interview_analysis': {'queue': 'analysis'},
        'tasks.generate_report': {'queue': 'reports'}
    }
)

@celery_app.task(name="tasks.run_interview_analysis", bind=True)
def run_interview_analysis_task(self, conversation_history: list, job_description_text: list):
    """
    Tâche Celery appelée par l'API ML pour traiter l'analyse d'entretien.
    """
    print(f"Démarrage de la tâche d'analyse d'entretien - Task ID: {self.request.id}")
    
    try:
        # Simulation d'un traitement long
        import time
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 5, 'status': 'Initialisation...'})
        time.sleep(2)
        
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 5, 'status': 'Analyse en cours...'})
        time.sleep(5)
        
        self.update_state(state='PROGRESS', meta={'current': 4, 'total': 5, 'status': 'Finalisation...'})
        time.sleep(2)
        
        # Résultat simulé
        result = {
            "status": "completed",
            "task_id": self.request.id,
            "analysis": {
                "sentiment_score": 0.85,
                "key_insights": [
                    "Candidat motivé et expérimenté",
                    "Bonnes compétences techniques",
                    "Excellente communication"
                ],
                "recommendations": [
                    "Poursuivre le processus de recrutement",
                    "Organiser un entretien technique approfondi"
                ]
            },
            "conversation_length": len(conversation_history),
            "job_match_score": 0.78,
            "processed_at": "2025-07-15T10:30:00Z"
        }
        
        print("Analyse terminée avec succès")
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        print(error_msg)
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(name="tasks.generate_report", bind=True)
def generate_report_task(self, analysis_data: dict):
    """
    Tâche pour générer un rapport détaillé à partir des données d'analyse.
    """
    print(f"Génération du rapport en cours - Task ID: {self.request.id}")
    
    try:
        # Simulation de génération de rapport
        import time
        
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3, 'status': 'Préparation du rapport...'})
        time.sleep(3)
        
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 3, 'status': 'Génération du contenu...'})
        time.sleep(4)
        
        report = {
            "report_id": f"RPT_{analysis_data.get('candidate_id', 'unknown')}",
            "generated_at": "2025-07-15T10:30:00Z",
            "task_id": self.request.id,
            "summary": "Rapport d'analyse d'entretien généré avec succès",
            "detailed_analysis": analysis_data,
            "status": "completed"
        }
        
        print("Rapport généré avec succès")
        return report
        
    except Exception as e:
        error_msg = f"Erreur lors de la génération du rapport: {str(e)}"
        print(error_msg)
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        raise self.retry(exc=e, countdown=60, max_retries=3)
