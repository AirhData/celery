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

# Formatage de l'URL pour Celery
broker_url = f"rediss://:{UPSTASH_REDIS_TOKEN}@{UPSTASH_REDIS_URL.replace('https://', '')}"

celery_app = Celery(
    'worker_celery',
    broker=broker_url,
    backend=broker_url,
    broker_connection_retry_on_startup=True
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Paris',
    enable_utc=True,
    broker_use_ssl={'ssl_cert_reqs': 'CERT_NONE'},
    redis_backend_use_ssl={'ssl_cert_reqs': 'CERT_NONE'}
)

@celery_app.task(name="tasks.run_interview_analysis")
def run_interview_analysis_task(conversation_history: list, job_description_text: list):
    """
    Tâche Celery appelée par l'API ML pour traiter l'analyse d'entretien.
    Cette tâche peut faire des appels à l'API ML si nécessaire.
    """
    print("Démarrage de la tâche d'analyse d'entretien...")
    
    try:
        # Ici vous pouvez soit :
        # 1. Traiter directement avec vos modèles (si vous les avez dans cette API)
        # 2. Faire des appels à l'API ML pour des traitements spécifiques
        # 3. Utiliser CrewAI pour générer des rapports
        
        # Exemple : simulation d'un traitement long
        import time
        print("Simulation du traitement d'analyse...")
        time.sleep(10)  # Simulation de 10 secondes de traitement
        
        # Si vous devez faire appel à l'API ML pour certains traitements :
        # ml_response = requests.post(
        #     f"{ML_API_BASE_URL}/specific-analysis",
        #     json={
        #         "conversation_history": conversation_history,
        #         "job_description_text": job_description_text
        #     },
        #     timeout=300
        # )
        
        # Résultat simulé
        result = {
            "status": "completed",
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
            "job_match_score": 0.78
        }
        
        print("Analyse terminée avec succès")
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        print(error_msg)
        return {"error": error_msg, "status": "failed"}

@celery_app.task(name="tasks.generate_report")
def generate_report_task(analysis_data: dict):
    """
    Tâche pour générer un rapport détaillé à partir des données d'analyse.
    """
    print("Génération du rapport en cours...")
    
    try:
        # Simulation de génération de rapport
        import time
        time.sleep(5)
        
        report = {
            "report_id": f"RPT_{analysis_data.get('candidate_id', 'unknown')}",
            "generated_at": "2025-07-15T10:30:00Z",
            "summary": "Rapport d'analyse d'entretien généré avec succès",
            "detailed_analysis": analysis_data,
            "pdf_url": f"{ML_API_BASE_URL}/reports/download/123"
        }
        
        print("Rapport généré avec succès")
        return report
        
    except Exception as e:
        error_msg = f"Erreur lors de la génération du rapport: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
