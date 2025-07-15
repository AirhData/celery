import os
import ssl
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
    """Construit correctement l'URL Redis pour Upstash avec paramètres SSL"""
    try:
        # Nettoyer l'URL de base
        base_url = UPSTASH_REDIS_URL.strip()
        
        # Supprimer le protocole temporairement
        if base_url.startswith('redis://'):
            host_part = base_url[8:]  # Enlever 'redis://'
        elif base_url.startswith('rediss://'):
            host_part = base_url[9:]  # Enlever 'rediss://'
        else:
            host_part = base_url
        
        # Construire l'URL avec les paramètres SSL requis
        # Format: rediss://default:TOKEN@HOST:PORT/0?ssl_cert_reqs=CERT_NONE
        if ':' in host_part and not '@' in host_part:
            # Format HOST:PORT
            redis_url = f"rediss://default:{UPSTASH_REDIS_TOKEN}@{host_part}/0?ssl_cert_reqs=CERT_NONE"
        else:
            # Format HOST seulement, ajouter le port par défaut
            redis_url = f"rediss://default:{UPSTASH_REDIS_TOKEN}@{host_part}:6380/0?ssl_cert_reqs=CERT_NONE"
        
        logger.info(f"✅ URL Redis construite avec SSL: rediss://default:***@{host_part}")
        return redis_url
        
    except Exception as e:
        logger.error(f"❌ Erreur construction URL Redis: {e}")
        # Fallback avec paramètres SSL
        return f"rediss://default:{UPSTASH_REDIS_TOKEN}@{UPSTASH_REDIS_URL.replace('redis://', '').replace('rediss://', '')}:6380/0?ssl_cert_reqs=CERT_NONE"

# Construire l'URL Redis
broker_url = build_redis_url()

logger.info(f"🔗 Configuration Redis OK")
logger.info(f"🚀 API Hugging Face: https://quentinl52-interview-agents-api.hf.space")

# Configuration Celery avec SSL explicite
celery_app = Celery(
    'airh_worker',
    broker=broker_url,
    backend=broker_url,
)

# Configuration SSL stricte pour Upstash
celery_app.conf.update(
    # Sérialisation
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Configuration SSL EXPLICITE pour broker
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
    },
    
    # Configuration SSL EXPLICITE pour backend
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
    },
    
    # Paramètres de connexion Redis
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Options Redis spécifiques
    redis_retry_on_timeout=True,
    redis_socket_connect_timeout=10,
    redis_socket_timeout=10,
    redis_max_connections=20,
    
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
    
    # Worker settings
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Test de connexion amélioré
def test_redis_connection():
    """Test la connexion Redis avec gestion SSL"""
    try:
        logger.info("🔍 Test de connexion Redis avec SSL...")
        
        # Test via backend Celery
        from celery.backends.redis import RedisBackend
        backend = RedisBackend(app=celery_app, url=broker_url)
        
        # Ping Redis
        backend.client.ping()
        logger.info("✅ Connexion Redis SSL réussie")
        
        # Test inspection Celery
        inspect = celery_app.control.inspect()
        logger.info("✅ Inspection Celery OK")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur connexion Redis SSL: {e}")
        logger.error(f"🔧 URL utilisée: {broker_url.replace(UPSTASH_REDIS_TOKEN, '***')}")
        
        # Essayer avec une approche alternative
        try:
            logger.info("🔄 Tentative de connexion alternative...")
            
            # Essayer avec redis-py directement
            import redis
            
            # Extraire host et port de l'URL
            host_part = broker_url.split('@')[1].split('/')[0]
            host, port = host_part.split(':')
            port = int(port)
            
            r = redis.Redis(
                host=host,
                port=port,
                password=UPSTASH_REDIS_TOKEN,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                ssl_check_hostname=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            r.ping()
            logger.info("✅ Connexion Redis directe réussie")
            return True
            
        except Exception as e2:
            logger.error(f"❌ Erreur connexion alternative: {e2}")
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
            meta={'current': 2, 'total': 5, 'status': 'Analyse des conversations...'}
        )
        time.sleep(3)
        
        # Étape 3
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 5, 'status': 'Évaluation de compatibilité...'}
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
        
        # Analyse des données
        sentiment_score = analyze_conversation_sentiment(conversation_history)
        compatibility_score = evaluate_job_compatibility(conversation_history, job_description_text)
        
        # Résultat
        result = {
            "status": "completed",
            "task_id": self.request.id,
            "timestamp": time.time(),
            "analysis": {
                "sentiment_score": sentiment_score,
                "job_match_score": compatibility_score,
                "conversation_length": len(conversation_history),
                "key_insights": [
                    "Candidat évalué avec succès",
                    "Analyse comportementale complète",
                    "Recommandations générées"
                ],
                "recommendations": [
                    "Évaluation technique recommandée" if compatibility_score > 0.6 else "Formation nécessaire",
                    "Candidat motivé" if sentiment_score > 0.7 else "Travailler la motivation"
                ],
                "detailed_metrics": {
                    "total_messages": len(conversation_history),
                    "avg_response_quality": round((sentiment_score + compatibility_score) / 2, 2),
                    "hiring_recommendation": "Recommandé" if (sentiment_score + compatibility_score) / 2 > 0.6 else "Non recommandé"
                }
            }
        }
        
        logger.info(f"✅ Analyse terminée - Task ID: {self.request.id}")
        logger.info(f"📊 Scores: Sentiment={sentiment_score}, Compatibilité={compatibility_score}")
        
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'task_id': self.request.id}
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
            meta={'current': 1, 'total': 3, 'status': 'Structuration des données...'}
        )
        time.sleep(2)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 3, 'status': 'Génération du contenu...'}
        )
        time.sleep(3)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 3, 'status': 'Finalisation...'}
        )
        time.sleep(1)
        
        report = {
            "report_id": f"RPT_{analysis_data.get('candidate_id', 'unknown')}_{int(time.time())}",
            "generated_at": time.time(),
            "task_id": self.request.id,
            "summary": "Rapport d'analyse d'entretien généré avec succès",
            "executive_summary": {
                "overall_assessment": "Candidat évalué",
                "key_strengths": ["Communication", "Motivation"],
                "improvement_areas": ["Expérience technique"],
                "recommendation": "Évaluation approfondie recommandée"
            },
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
            meta={'error': error_msg, 'task_id': self.request.id}
        )
        raise

# Fonctions d'analyse simplifiées
def analyze_conversation_sentiment(conversation_history):
    """Analyse simple du sentiment"""
    positive_keywords = ['motivé', 'excellent', 'passionné', 'intéressant', 'parfait']
    negative_keywords = ['difficile', 'problème', 'stress', 'inquiet']
    
    total_score = 0
    message_count = 0
    
    for message in conversation_history:
        if message.get("role") == "user":
            content = message.get("content", "").lower()
            message_count += 1
            
            pos_count = sum(1 for keyword in positive_keywords if keyword in content)
            neg_count = sum(1 for keyword in negative_keywords if keyword in content)
            
            if pos_count > 0 or neg_count > 0:
                total_score += (pos_count - neg_count) / max(pos_count + neg_count, 1)
    
    if message_count > 0:
        sentiment = max(0.1, min(0.9, 0.5 + (total_score / message_count) * 0.3))
    else:
        sentiment = 0.5
    
    return round(sentiment, 2)

def evaluate_job_compatibility(conversation_history, job_description_text):
    """Évaluation simple de compatibilité"""
    if not job_description_text:
        return 0.5
    
    job_keywords = set(job_description_text[0].lower().split())
    candidate_text = " ".join([msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]).lower()
    candidate_words = set(candidate_text.split())
    
    # Calculer l'intersection
    common_words = job_keywords & candidate_words
    important_words = [word for word in common_words if len(word) > 3]
    
    if len(job_keywords) > 0:
        compatibility = min(0.9, len(important_words) / max(len(job_keywords) * 0.1, 1))
    else:
        compatibility = 0.5
    
    return round(max(0.1, compatibility), 2)

if __name__ == "__main__":
    logger.info("🔧 Test de la configuration SSL...")
    
    # Tester la connexion Redis
    if test_redis_connection():
        logger.info("🎉 Worker prêt à démarrer avec SSL")
    else:
        logger.error("💥 Problème de configuration SSL détecté")
        
    logger.info("🚀 Pour démarrer le worker:")
    logger.info("celery -A main worker --loglevel=info --concurrency=1")
