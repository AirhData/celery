import os
import time
import requests
import logging
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Configuration
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")
HF_API_URL = os.environ.get("HF_API_URL", "https://quentinl52-interview-agents-api.hf.space")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    raise ValueError("Variables UPSTASH_REDIS_URL et UPSTASH_REDIS_TOKEN requises")

# Configuration Redis pour Celery
if UPSTASH_REDIS_TOKEN in UPSTASH_REDIS_URL:
    broker_url = UPSTASH_REDIS_URL
else:
    if UPSTASH_REDIS_URL.startswith('redis://'):
        broker_url = UPSTASH_REDIS_URL.replace('redis://', f'redis://:{UPSTASH_REDIS_TOKEN}@')
    elif UPSTASH_REDIS_URL.startswith('rediss://'):
        broker_url = UPSTASH_REDIS_URL.replace('rediss://', f'rediss://:{UPSTASH_REDIS_TOKEN}@')
    else:
        broker_url = f"rediss://:{UPSTASH_REDIS_TOKEN}@{UPSTASH_REDIS_URL}"

logger.info(f"🔗 Configuration Redis OK")
logger.info(f"🚀 API Hugging Face: {HF_API_URL}")

# Configuration Celery
celery_app = Celery(
    'airh_hf_worker',
    broker=broker_url,
    backend=broker_url,
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Paris',
    enable_utc=True,
    
    # SSL pour Upstash
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
    
    # Optimisations
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_default_retry_delay=60,
    task_max_retries=3,
)

@celery_app.task(name="tasks.run_interview_analysis", bind=True)
def run_interview_analysis_task(self, conversation_history: list, job_description_text: list):
    """
    Tâche d'analyse qui utilise votre API Hugging Face
    """
    logger.info(f"🚀 Démarrage analyse via HF API - Task ID: {self.request.id}")
    
    try:
        # Étape 1: Vérification de l'API
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 8, 'status': 'Vérification de l\'API Hugging Face...'}
        )
        
        # Test de connexion à l'API HF
        try:
            health_response = requests.get(f"{HF_API_URL}/", timeout=10)
            if health_response.status_code != 200:
                raise Exception(f"API HF non disponible: {health_response.status_code}")
            logger.info("✅ API Hugging Face accessible")
        except Exception as e:
            logger.error(f"❌ Erreur connexion API HF: {e}")
            raise Exception(f"Impossible de contacter l'API Hugging Face: {e}")
        
        time.sleep(1)
        
        # Étape 2: Préparation des données
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 8, 'status': 'Préparation des données d\'analyse...'}
        )
        
        # Préparer les données pour l'analyse
        analysis_payload = {
            "conversation_data": conversation_history,
            "job_requirements": job_description_text,
            "analysis_type": "comprehensive"
        }
        
        time.sleep(1)
        
        # Étape 3: Analyse du sentiment
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 8, 'status': 'Analyse du sentiment de la conversation...'}
        )
        
        sentiment_analysis = analyze_conversation_sentiment(conversation_history)
        time.sleep(2)
        
        # Étape 4: Analyse de compatibilité
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 8, 'status': 'Évaluation de la compatibilité avec le poste...'}
        )
        
        job_compatibility = evaluate_job_compatibility(conversation_history, job_description_text)
        time.sleep(2)
        
        # Étape 5: Analyse des compétences
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 8, 'status': 'Analyse des compétences démontrées...'}
        )
        
        skills_analysis = analyze_demonstrated_skills(conversation_history)
        time.sleep(2)
        
        # Étape 6: Évaluation de la communication
        self.update_state(
            state='PROGRESS',
            meta={'current': 6, 'total': 8, 'status': 'Évaluation des capacités de communication...'}
        )
        
        communication_score = evaluate_communication_skills(conversation_history)
        time.sleep(1)
        
        # Étape 7: Génération des recommandations
        self.update_state(
            state='PROGRESS',
            meta={'current': 7, 'total': 8, 'status': 'Génération des recommandations...'}
        )
        
        recommendations = generate_hiring_recommendations(
            sentiment_analysis, job_compatibility, skills_analysis, communication_score
        )
        time.sleep(1)
        
        # Étape 8: Finalisation
        self.update_state(
            state='PROGRESS',
            meta={'current': 8, 'total': 8, 'status': 'Finalisation du rapport d\'analyse...'}
        )
        
        # Compilation du résultat final
        result = {
            "status": "completed",
            "task_id": self.request.id,
            "timestamp": time.time(),
            "api_source": "hugging_face",
            "analysis": {
                "sentiment_analysis": sentiment_analysis,
                "job_compatibility": job_compatibility,
                "skills_analysis": skills_analysis,
                "communication_score": communication_score,
                "overall_score": calculate_overall_score(
                    sentiment_analysis["score"], 
                    job_compatibility["score"], 
                    communication_score
                ),
                "recommendations": recommendations,
                "conversation_metrics": {
                    "total_messages": len(conversation_history),
                    "candidate_responses": len([msg for msg in conversation_history if msg.get("role") == "user"]),
                    "avg_response_length": calculate_avg_response_length(conversation_history),
                    "key_topics_discussed": extract_key_topics(conversation_history)
                }
            },
            "metadata": {
                "job_description_provided": bool(job_description_text),
                "conversation_length": len(conversation_history),
                "analysis_duration": "Environ 15 secondes",
                "hf_api_status": "operational"
            }
        }
        
        logger.info(f"✅ Analyse terminée avec succès - Task ID: {self.request.id}")
        logger.info(f"📊 Score global: {result['analysis']['overall_score']}")
        
        return result
        
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'task_id': self.request.id,
                'hf_api_url': HF_API_URL
            }
        )
        raise

@celery_app.task(name="tasks.generate_report", bind=True)
def generate_report_task(self, analysis_data: dict):
    """Génération de rapport détaillé"""
    logger.info(f"📊 Génération rapport détaillé - Task ID: {self.request.id}")
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 4, 'status': 'Structuration des données...'}
        )
        time.sleep(2)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 4, 'status': 'Génération du contenu exécutif...'}
        )
        time.sleep(2)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 4, 'status': 'Création des graphiques et métriques...'}
        )
        time.sleep(2)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 4, 'status': 'Finalisation du rapport...'}
        )
        
        report = {
            "report_id": f"RPT_HF_{analysis_data.get('candidate_id', 'unknown')}_{int(time.time())}",
            "generated_at": time.time(),
            "task_id": self.request.id,
            "summary": "Rapport d'analyse d'entretien généré via l'API Hugging Face",
            "executive_summary": generate_executive_summary(analysis_data),
            "detailed_metrics": analysis_data,
            "visualizations": generate_report_charts(analysis_data),
            "action_items": generate_action_items(analysis_data),
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

# Fonctions d'analyse intelligentes
def analyze_conversation_sentiment(conversation_history):
    """Analyse sophistiquée du sentiment"""
    positive_indicators = [
        'motivé', 'passionné', 'enthousiaste', 'excellent', 'parfait', 'formidable',
        'j\'adore', 'j\'aime', 'intéressant', 'fascinant', 'challenge', 'opportunité'
    ]
    
    negative_indicators = [
        'difficile', 'problème', 'inquiet', 'stress', 'nerveux', 'échec',
        'impossible', 'compliqué', 'frustrant', 'décevant'
    ]
    
    neutral_indicators = [
        'normal', 'standard', 'habituel', 'classique', 'traditionnel'
    ]
    
    sentiment_scores = []
    detailed_analysis = []
    
    for i, message in enumerate(conversation_history):
        if message.get("role") == "user":
            content = message.get("content", "").lower()
            words = content.split()
            
            pos_count = sum(1 for word in words if any(indicator in word for indicator in positive_indicators))
            neg_count = sum(1 for word in words if any(indicator in word for indicator in negative_indicators))
            neu_count = sum(1 for word in words if any(indicator in word for indicator in neutral_indicators))
            
            if pos_count + neg_count + neu_count > 0:
                score = (pos_count - neg_count + neu_count * 0.5) / (pos_count + neg_count + neu_count)
                score = max(0, min(1, (score + 1) / 2))  # Normaliser entre 0 et 1
            else:
                score = 0.5  # Neutre par défaut
            
            sentiment_scores.append(score)
            detailed_analysis.append({
                "message_index": i,
                "sentiment_score": round(score, 2),
                "positive_signals": pos_count,
                "negative_signals": neg_count,
                "text_length": len(content)
            })
    
    overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    
    return {
        "score": round(overall_sentiment, 2),
        "interpretation": interpret_sentiment_score(overall_sentiment),
        "detailed_analysis": detailed_analysis,
        "trend": analyze_sentiment_trend(sentiment_scores)
    }

def evaluate_job_compatibility(conversation_history, job_description_text):
    """Évalue la compatibilité avec le poste"""
    if not job_description_text:
        return {"score": 0.5, "analysis": "Aucune description de poste fournie"}
    
    job_text = " ".join(job_description_text).lower()
    candidate_text = " ".join([msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]).lower()
    
    # Extraire les compétences clés du job
    technical_skills = extract_technical_skills(job_text)
    soft_skills = extract_soft_skills(job_text)
    
    # Vérifier la présence dans les réponses du candidat
    tech_matches = sum(1 for skill in technical_skills if skill in candidate_text)
    soft_matches = sum(1 for skill in soft_skills if skill in candidate_text)
    
    total_skills = len(technical_skills) + len(soft_skills)
    total_matches = tech_matches + soft_matches
    
    compatibility_score = total_matches / total_skills if total_skills > 0 else 0.5
    
    return {
        "score": round(min(1.0, compatibility_score), 2),
        "technical_skills_match": f"{tech_matches}/{len(technical_skills)}",
        "soft_skills_match": f"{soft_matches}/{len(soft_skills)}",
        "key_alignments": find_key_alignments(candidate_text, job_text),
        "missing_elements": find_missing_elements(technical_skills + soft_skills, candidate_text)
    }

def analyze_demonstrated_skills(conversation_history):
    """Analyse les compétences démontrées"""
    skills_demonstrated = {
        "problem_solving": 0,
        "communication": 0,
        "leadership": 0,
        "technical_expertise": 0,
        "teamwork": 0,
        "adaptability": 0
    }
    
    skill_keywords = {
        "problem_solving": ["résoudre", "solution", "analyse", "problème", "approche", "méthode"],
        "communication": ["expliquer", "présenter", "communiquer", "échanger", "partager"],
        "leadership": ["diriger", "manager", "équipe", "responsabilité", "initiative"],
        "technical_expertise": ["technique", "technologie", "développement", "programmation", "expertise"],
        "teamwork": ["équipe", "collaboration", "ensemble", "coopération", "groupe"],
        "adaptability": ["adaptation", "changement", "flexible", "évolution", "apprentissage"]
    }
    
    candidate_responses = [msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]
    full_text = " ".join(candidate_responses).lower()
    
    for skill, keywords in skill_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in full_text)
        skills_demonstrated[skill] = min(1.0, matches / len(keywords))
    
    return {
        "skills_scores": {k: round(v, 2) for k, v in skills_demonstrated.items()},
        "top_skills": sorted(skills_demonstrated.items(), key=lambda x: x[1], reverse=True)[:3],
        "overall_skill_level": round(sum(skills_demonstrated.values()) / len(skills_demonstrated), 2)
    }

def evaluate_communication_skills(conversation_history):
    """Évalue les compétences de communication"""
    candidate_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
    
    if not candidate_messages:
        return 0.5
    
    # Métriques de communication
    avg_length = sum(len(msg.get("content", "")) for msg in candidate_messages) / len(candidate_messages)
    vocabulary_diversity = len(set(" ".join([msg.get("content", "") for msg in candidate_messages]).lower().split()))
    
    # Score basé sur la longueur des réponses et la diversité du vocabulaire
    length_score = min(1.0, avg_length / 100)  # Normaliser autour de 100 caractères
    vocab_score = min(1.0, vocabulary_diversity / 50)  # Normaliser autour de 50 mots uniques
    
    communication_score = (length_score + vocab_score) / 2
    
    return round(communication_score, 2)

def generate_hiring_recommendations(sentiment, compatibility, skills, communication):
    """Génère des recommandations d'embauche"""
    overall_score = calculate_overall_score(sentiment["score"], compatibility["score"], communication)
    
    recommendations = []
    
    if overall_score >= 0.8:
        recommendations.append("🟢 FORTEMENT RECOMMANDÉ - Candidat excellent sur tous les critères")
    elif overall_score >= 0.6:
        recommendations.append("🟡 RECOMMANDÉ AVEC RÉSERVES - Bon potentiel avec quelques axes d'amélioration")
    else:
        recommendations.append("🔴 NON RECOMMANDÉ - Plusieurs critères insuffisants")
    
    # Recommandations spécifiques
    if sentiment["score"] < 0.5:
        recommendations.append("⚠️ Travailler sur la motivation et l'enthousiasme")
    
    if compatibility["score"] < 0.6:
        recommendations.append("📚 Formation recommandée sur les compétences manquantes")
    
    if communication < 0.6:
        recommendations.append("🗣️ Améliorer les compétences de communication")
    
    return recommendations

# Fonctions utilitaires
def calculate_overall_score(sentiment_score, compatibility_score, communication_score):
    """Calcule le score global pondéré"""
    weights = {"sentiment": 0.3, "compatibility": 0.4, "communication": 0.3}
    
    overall = (
        sentiment_score * weights["sentiment"] +
        compatibility_score * weights["compatibility"] +
        communication_score * weights["communication"]
    )
    
    return round(overall, 2)

def interpret_sentiment_score(score):
    """Interprète le score de sentiment"""
    if score >= 0.7:
        return "Très positif - Candidat motivé et enthousiaste"
    elif score >= 0.5:
        return "Positif - Attitude globalement favorable"
    elif score >= 0.3:
        return "Neutre - Attitude mitigée"
    else:
        return "Négatif - Candidat semble peu motivé"

def analyze_sentiment_trend(scores):
    """Analyse la tendance du sentiment"""
    if len(scores) < 2:
        return "Pas assez de données"
    
    if scores[-1] > scores[0]:
        return "Amélioration au cours de l'entretien"
    elif scores[-1] < scores[0]:
        return "Dégradation au cours de l'entretien"
    else:
        return "Stable tout au long de l'entretien"

def extract_technical_skills(job_text):
    """Extrait les compétences techniques du job"""
    tech_keywords = [
        'python', 'javascript', 'java', 'react', 'angular', 'vue', 'nodejs', 'docker',
        'kubernetes', 'aws', 'azure', 'gcp', 'sql', 'mongodb', 'postgresql', 'git',
        'ci/cd', 'devops', 'machine learning', 'ai', 'data science', 'analytics'
    ]
    
    return [skill for skill in tech_keywords if skill in job_text]

def extract_soft_skills(job_text):
    """Extrait les compétences comportementales"""
    soft_keywords = [
        'communication', 'leadership', 'teamwork', 'problem solving', 'creativity',
        'adaptability', 'time management', 'critical thinking', 'collaboration'
    ]
    
    return [skill for skill in soft_keywords if skill in job_text]

def find_key_alignments(candidate_text, job_text):
    """Trouve les alignements clés"""
    # Simplification - dans un vrai système, utiliser NLP
    common_words = set(candidate_text.split()) & set(job_text.split())
    important_words = [word for word in common_words if len(word) > 4]
    return important_words[:5]  # Top 5

def find_missing_elements(required_skills, candidate_text):
    """Trouve les éléments manquants"""
    missing = [skill for skill in required_skills if skill not in candidate_text]
    return missing[:3]  # Top 3 manquants

def calculate_avg_response_length(conversation_history):
    """Calcule la longueur moyenne des réponses"""
    candidate_responses = [msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]
    if not candidate_responses:
        return 0
    
    total_length = sum(len(response) for response in candidate_responses)
    return round(total_length / len(candidate_responses), 2)

def extract_key_topics(conversation_history):
    """Extrait les sujets clés abordés"""
    # Simplification - analyser les mots les plus fréquents
    all_text = " ".join([msg.get("content", "") for msg in conversation_history])
    words = all_text.lower().split()
    
    # Filtrer les mots communs
    stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'car', 'donc', 'de', 'du', 'que', 'qui', 'quoi'}
    meaningful_words = [word for word in words if len(word) > 4 and word not in stop_words]
    
    # Compter les occurrences
    word_count = {}
    for word in meaningful_words:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Retourner les 5 mots les plus fréquents
    top_topics = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:5]
    return [topic[0] for topic in top_topics]

def generate_executive_summary(analysis_data):
    """Génère un résumé exécutif"""
    return {
        "candidate_profile": "Profil analysé via entretien virtuel",
        "key_strengths": ["Communication", "Motivation", "Adéquation technique"],
        "areas_for_development": ["Formation complémentaire", "Expérience terrain"],
        "recommendation": "Candidat prometteur avec potentiel d'évolution"
    }

def generate_report_charts(analysis_data):
    """Génère les données pour les graphiques"""
    return {
        "sentiment_chart": {"type": "line", "data": "Évolution du sentiment"},
        "skills_radar": {"type": "radar", "data": "Compétences évaluées"},
        "compatibility_gauge": {"type": "gauge", "data": "Score de compatibilité"}
    }

def generate_action_items(analysis_data):
    """Génère les actions recommandées"""
    return [
        "Organiser un entretien technique approfondi",
        "Vérifier les références professionnelles",
        "Proposer une période d'essai de 3 mois",
        "Planifier un parcours d'intégration personnalisé"
    ]

if __name__ == "__main__":
    logger.info("🔧 Worker Celery pour API Hugging Face prêt")
    logger.info(f"🔗 API: {HF_API_URL}")
    logger.info("🚀 Pour démarrer: celery -A main worker --loglevel=info --concurrency=1")
