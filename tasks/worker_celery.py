import os
import json
from celery import Celery
from crewai import Crew, Process
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# --- Import des modules de votre application ---
from src.deep_learning_analyzer import MultiModelInterviewAnalyzer
from src.rag_handler import RAGHandler
from src.crew.agents import report_generator_agent
from src.crew.tasks import generate_report_task

# --- Configuration de Celery avec Upstash ---
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")

if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    raise ValueError("Les variables d'environnement UPSTASH_REDIS_URL et UPSTASH_REDIS_TOKEN sont requises.")

# Formatage de l'URL pour Celery (rediss://:<token>@<host>)
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
    """Tâche Celery qui exécute l'analyse complète de l'entretien."""
    print("Démarrage de la tâche d'analyse...")
    # Votre logique d'analyse IA reste ici
    analyzer = MultiModelInterviewAnalyzer()
    structured_analysis = analyzer.run_full_analysis(conversation_history, job_description_text)
    rag_handler = RAGHandler()
    rag_feedback = []
    if structured_analysis.get("intent_analysis"):
        for intent in structured_analysis["intent_analysis"]:
            query = f"Conseils pour un candidat qui cherche à {intent['labels'][0]}"
            rag_feedback.extend(rag_handler.get_relevant_feedback(query))
    unique_feedback = list(set(rag_feedback))
    interview_crew = Crew(
        agents=[report_generator_agent],
        tasks=[generate_report_task],
        process=Process.sequential,
        verbose=False,
        telemetry=False
    )
    final_report = interview_crew.kickoff(inputs={
        'structured_analysis_data': json.dumps(structured_analysis, indent=2, ensure_ascii=False),
        'rag_contextual_feedback': "\n- ".join(unique_feedback)
    })
    print("Analyse terminée.")
    return final_report
