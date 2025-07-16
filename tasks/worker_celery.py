import os
import ssl
import logging
from celery import Celery
from kombu import Queue
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Upstash
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")

if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    raise ValueError("Variables UPSTASH_REDIS_URL et UPSTASH_REDIS_TOKEN requises")

def build_upstash_url():
    """Construit l'URL Redis Upstash avec la méthode recommandée"""
    try:
        # Méthode 1: URL complète au format Upstash standard
        # Format recommandé par Upstash: rediss://:password@endpoint:port
        
        # Nettoyer l'endpoint
        endpoint = UPSTASH_REDIS_URL.strip()
        
        # Supprimer les protocoles existants
        for protocol in ['rediss://', 'redis://', 'https://', 'http://']:
            if endpoint.startswith(protocol):
                endpoint = endpoint[len(protocol):]
        
        # Supprimer les credentials existants (format user:pass@)
        if '@' in endpoint:
            endpoint = endpoint.split('@')[-1]
        
        # Construire l'URL finale
        # Format Upstash: rediss://:token@host:port
        redis_url = f"rediss://:{UPSTASH_REDIS_TOKEN}@{endpoint}"
        
        # Ajouter le port si manquant
        if ':' not in endpoint:
            redis_url = f"rediss://:{UPSTASH_REDIS_TOKEN}@{endpoint}:6380"
        
        logger.info(f"✅ URL Upstash construite: rediss://:***@{endpoint}")
        return redis_url
        
    except Exception as e:
        logger.error(f"❌ Erreur construction URL: {e}")
        # Fallback
        return f"rediss://:{UPSTASH_REDIS_TOKEN}@{UPSTASH_REDIS_URL}:6380"

# Construire l'URL
broker_url = build_upstash_url()

# Configuration Celery pour Upstash
celery_app = Celery('upstash_worker')

# Configuration spécifique Upstash
celery_app.conf.update(
    # URLs
    broker_url=broker_url,
    result_backend=broker_url,
    
    # Sérialisation
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Configuration SSL pour Upstash (plus permissive)
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
        'ssl_ciphers': None,
    },
    
    # Configuration backend SSL
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
        'ssl_check_hostname': False,
    },
    
    # Paramètres de connexion robustes pour Upstash
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=50,  # Augmenté
    broker_connection_retry_delay=1.0,
    
    # Paramètres Redis spécifiques
    redis_max_connections=10,  # Réduit pour Upstash
    redis_socket_timeout=30,   # Augmenté
    redis_socket_connect_timeout=30,  # Augmenté
    redis_retry_on_timeout=True,
    redis_health_check_interval=30,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Timeouts
    task_soft_time_limit=300,
    task_time_limit=600,
    result_expires=3600,
    
    # Heartbeat (important pour Upstash)
    broker_heartbeat=None,  # Désactiver le heartbeat
    worker_disable_rate_limits=True,
    
    # Task routing
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)

# Test de connexion amélioré
def test_upstash_connection():
    """Test spécifique pour Upstash Redis"""
    try:
        logger.info("🔍 Test de connexion Upstash Redis...")
        
        # Test avec redis-py directement
        import redis
        
        # Parser l'URL pour extraire les composants
        url_parts = broker_url.replace('rediss://', '').replace('redis://', '')
        
        if '@' in url_parts:
            auth_part, host_part = url_parts.split('@', 1)
            password = auth_part.split(':', 1)[1] if ':' in auth_part else auth_part
        else:
            password = UPSTASH_REDIS_TOKEN
            host_part = url_parts
        
        if ':' in host_part:
            host, port = host_part.split(':', 1)
            port = int(port)
        else:
            host = host_part
            port = 6380
        
        # Connexion Redis directe
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_check_hostname=False,
            socket_connect_timeout=10,
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=5
        )
        
        # Test ping
        response = r.ping()
        logger.info(f"✅ Ping Redis réussi: {response}")
        
        # Test set/get
        r.set('test_key', 'test_value', ex=60)
        value = r.get('test_key')
        logger.info(f"✅ Test set/get réussi: {value}")
        
        # Test Celery
        from celery.backends.redis import RedisBackend
        backend = RedisBackend(app=celery_app, url=broker_url)
        backend.client.ping()
        logger.info("✅ Backend Celery OK")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test Upstash: {e}")
        logger.error(f"🔧 Host: {host if 'host' in locals() else 'unknown'}")
        logger.error(f"🔧 Port: {port if 'port' in locals() else 'unknown'}")
        return False

@celery_app.task(name="tasks.run_interview_analysis", bind=True)
def run_interview_analysis_task(self, conversation_history: list, job_description_text: list):
    """Tâche d'analyse optimisée pour Upstash"""
    logger.info(f"🚀 Démarrage analyse Upstash - Task ID: {self.request.id}")
    
    try:
        import time
        
        # Progression avec états plus courts pour éviter les timeouts
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3, 'status': 'Début analyse...'})
        time.sleep(1)
        
        # Analyse rapide
        sentiment = analyze_sentiment_quick(conversation_history)
        compatibility = analyze_compatibility_quick(conversation_history, job_description_text)
        
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 3, 'status': 'Calcul scores...'})
        time.sleep(1)
        
        # Résultat
        result = {
            "status": "completed",
            "task_id": self.request.id,
            "timestamp": time.time(),
            "analysis": {
                "sentiment_score": sentiment,
                "job_match_score": compatibility,
                "overall_score": round((sentiment + compatibility) / 2, 2),
                "conversation_length": len(conversation_history),
                "recommendations": generate_recommendations(sentiment, compatibility),
                "insights": [
                    f"Sentiment: {'Positif' if sentiment > 0.6 else 'Neutre' if sentiment > 0.4 else 'Négatif'}",
                    f"Compatibilité: {'Élevée' if compatibility > 0.7 else 'Moyenne' if compatibility > 0.5 else 'Faible'}",
                    f"Recommandation: {'Poursuivre' if (sentiment + compatibility) / 2 > 0.6 else 'Évaluer davantage'}"
                ]
            }
        }
        
        self.update_state(state='PROGRESS', meta={'current': 3, 'total': 3, 'status': 'Terminé'})
        
        logger.info(f"✅ Analyse terminée - Score: {result['analysis']['overall_score']}")
        return result
        
    except Exception as e:
        error_msg = f"Erreur analyse: {str(e)}"
        logger.error(f"❌ {error_msg}")
        self.update_state(state='FAILURE', meta={'error': error_msg})
        raise

@celery_app.task(name="tasks.generate_report", bind=True)
def generate_report_task(self, analysis_data: dict):
    """Génération de rapport optimisée"""
    logger.info(f"📊 Génération rapport - Task ID: {self.request.id}")
    
    try:
        import time
        
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 2, 'status': 'Génération...'})
        time.sleep(2)
        
        report = {
            "report_id": f"RPT_{int(time.time())}",
            "generated_at": time.time(),
            "task_id": self.request.id,
            "summary": "Rapport généré avec succès",
            "data": analysis_data,
            "status": "completed"
        }
        
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 2, 'status': 'Terminé'})
        
        logger.info(f"✅ Rapport généré")
        return report
        
    except Exception as e:
        error_msg = f"Erreur rapport: {str(e)}"
        logger.error(f"❌ {error_msg}")
        self.update_state(state='FAILURE', meta={'error': error_msg})
        raise

# Fonctions d'analyse rapides
def analyze_sentiment_quick(conversation_history):
    """Analyse rapide du sentiment"""
    positive_words = ['motivé', 'excellent', 'bien', 'parfait', 'super']
    total_score = 0
    message_count = 0
    
    for msg in conversation_history:
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            message_count += 1
            score = sum(1 for word in positive_words if word in content)
            total_score += min(score, 1)  # Max 1 par message
    
    return round(total_score / max(message_count, 1), 2)

def analyze_compatibility_quick(conversation_history, job_description_text):
    """Analyse rapide de compatibilité"""
    if not job_description_text:
        return 0.5
    
    job_words = set(job_description_text[0].lower().split())
    candidate_text = " ".join([msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]).lower()
    candidate_words = set(candidate_text.split())
    
    common = job_words & candidate_words
    important_common = [w for w in common if len(w) > 3]
    
    return round(min(0.9, len(important_common) / max(len(job_words) * 0.2, 1)), 2)

def generate_recommendations(sentiment, compatibility):
    """Génère des recommandations"""
    recommendations = []
    
    if sentiment > 0.7 and compatibility > 0.7:
        recommendations.append("🟢 Candidat excellent - Recommandé pour embauche")
    elif sentiment > 0.5 and compatibility > 0.5:
        recommendations.append("🟡 Candidat prometteur - Entretien technique recommandé")
    else:
        recommendations.append("🔴 Candidat à évaluer davantage")
    
    if sentiment < 0.4:
        recommendations.append("⚠️ Travailler sur la motivation")
    if compatibility < 0.4:
        recommendations.append("📚 Formation nécessaire sur les compétences requises")
    
    return recommendations

if __name__ == "__main__":
    logger.info("🔧 Test configuration Upstash...")
    if test_upstash_connection():
        logger.info("🎉 Configuration Upstash OK - Worker prêt")
    else:
        logger.error("💥 Problème configuration Upstash")
    
    logger.info("🚀 Démarrage: celery -A main worker --loglevel=info --concurrency=1")
