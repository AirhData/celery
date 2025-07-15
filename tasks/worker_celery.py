import os
import logging
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Configuration Redis Upstash
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    raise ValueError("Variables UPSTASH_REDIS_URL et UPSTASH_REDIS_TOKEN requises")

def build_redis_url():
    """Construit correctement l'URL Redis pour Upstash"""
    try:
        # Cas 1: Si l'URL contient déjà le token (format complet)
        if "@" in UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN in UPSTASH_REDIS_URL:
            logger.info("✅ URL Redis complète détectée")
            return UPSTASH_REDIS_URL
        
        # Cas 2: URL de base, besoin d'ajouter le token
        # Format Upstash typique: redis://default:TOKEN@HOST:PORT
        
        # Nettoyer l'URL de base
        base_url = UPSTASH_REDIS_URL.strip()
        
        # Supprimer le protocole temporairement
        if base_url.startswith('redis://'):
            protocol = 'redis://'
            host_part = base_url[8:]  # Enlever 'redis://'
        elif base_url.startswith('rediss://'):
            protocol = 'rediss://'
            host_part = base_url[9:]  # Enlever 'rediss://'
        else:
            # Pas de protocole, ajouter rediss par défaut pour Upstash
            protocol = 'rediss://'
            host_part = base_url
        
        # Construire l'URL finale avec authentification
        # Format: rediss://default:TOKEN@HOST:PORT/0
        if ':' in host_part and not '@' in host_part:
            # Format HOST:PORT
            redis_url = f"{protocol}default:{UPSTASH_REDIS_TOKEN}@{host_part}/0"
        else:
            # Format HOST seulement, ajouter le port par défaut
            redis_url = f"{protocol}default:{UPSTASH_REDIS_TOKEN}@{host_part}:6380/0"
        
        logger.info(f"✅ URL Redis construite: {protocol}default:***@{host_part}")
        return redis_url
        
    except Exception as e:
        logger.error(f"❌ Erreur construction URL Redis: {e}")
        # Fallback vers une URL de base
        return f"rediss://default:{UPSTASH_REDIS_TOKEN}@{UPSTASH_REDIS_URL.replace('redis://', '').replace('rediss://', '')}:6380/0"

# Construire l'URL Redis
broker_url = build_redis_url()

logger.info(f"🔗 Configuration Redis OK")
logger.info(f"🚀 API Hugging Face: https://quentinl52-interview-agents-api.hf.space")

# Configuration Celery
celery_app = Celery(
    'airh_worker',
    broker=broker_url,
    backend=broker_url,
)

# Configuration SSL et paramètres pour Upstash
celery_app.conf.update(
    # Sérialisation
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Configuration SSL spécifique à Upstash Redis
    broker_use_ssl={
        'ssl_cert_reqs': None,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': None,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
    },
    
    # Paramètres de connexion Redis
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Gestion des tâches
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Résultats
    result_expires=3600,  # 1 heure
    result_compression='gzip',
    
    # Backend Redis spécifique
    redis_retry_on_timeout=True,
    redis_socket_connect_timeout=5,
    redis_socket_timeout=5,
)

# Test de connexion
def test_redis_connection():
    """Test la connexion Redis"""
    try:
        # Tester la connexion via Celery
        inspect = celery_app.control.inspect()
        
        # Ceci va tester la connexion Redis
        logger.info("🔍 Test de connexion Redis...")
        
        # Test simple de ping
        from celery.backends.redis import RedisBackend
        backend = RedisBackend(app=celery_app, url=broker_url)
        
        # Tester la connexion
        backend.client.ping()
        logger.info("✅ Connexion Redis réussie")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur connexion Redis: {e}")
        logger.error(f"🔧 URL utilisée: {broker_url.replace(UPSTASH_REDIS_TOKEN, '***')}")
        return False

@celery_app.task(name="tasks.run_interview_analysis", bind=True)
def run_interview_analysis_task(self, conversation_history: list, job_description_text: list):
    """Tâche d'analyse d'entretien"""
    logger.info(f"🚀 Démarrage analyse - Task ID: {self.request.id}")
    
    try:
        import time
        
        # Étape 1
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 5, 'status': 'Initialisation...'}
        )
        time.sleep(2)
        
        # Étape 2
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 5, 'status': 'Analyse en cours...'}
        )
        time.sleep(5)
        
        # Étape 3
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 5, 'status': 'Calcul des scores...'}
        )
        time.sleep(3)
        
        # Étape 4
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 5, 'status': 'Génération des insights...'}
        )
        time.sleep(2)
        
        # Étape 5
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 5, 'status': 'Finalisation...'}
        )
        time.sleep(1)
        
        # Résultat
        result = {
            "status": "completed",
            "task_id": self.request.id,
            "timestamp": time.time(),
            "analysis": {
                "sentiment_score": 0.85,
                "job_match_score": 0.78,
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
            "job_descriptions_count": len(job_description_text)
        }
        
        logger.info(f"✅ Analyse terminée - Task ID: {self.request.id}")
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'traceback': str(e)}
        )
        raise

@celery_app.task(name="tasks.generate_report", bind=True)
def generate_report_task(self, analysis_data: dict):
    """Génération de rapport"""
    logger.info(f"📊 Génération rapport - Task ID: {self.request.id}")
    
    try:
        import time
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 3, 'status': 'Préparation...'}
        )
        time.sleep(3)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 3, 'status': 'Génération...'}
        )
        time.sleep(4)
        
        report = {
            "report_id": f"RPT_{analysis_data.get('candidate_id', 'unknown')}_{int(time.time())}",
            "generated_at": time.time(),
            "task_id": self.request.id,
            "summary": "Rapport généré avec succès",
            "detailed_analysis": analysis_data,
            "status": "completed"
        }
        
        logger.info(f"✅ Rapport généré - Task ID: {self.request.id}")
        return report
        
    except Exception as e:
        error_msg = f"Erreur génération rapport: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'traceback': str(e)}
        )
        raise

if __name__ == "__main__":
    logger.info("🔧 Test de la configuration...")
    
    # Tester la connexion Redis
    if test_redis_connection():
        logger.info("🎉 Worker prêt à démarrer")
    else:
        logger.error("💥 Problème de configuration détecté")
        
    logger.info("🚀 Pour démarrer le worker:")
    logger.info("celery -A main worker --loglevel=info --concurrency=1")
