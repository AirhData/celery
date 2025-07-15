import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIrh Celery Worker Service",
    description="Service Celery pour le traitement des analyses d'entretien en arrière-plan",
    version="1.0.0"
)

# Import Celery avec gestion d'erreur
try:
    from celery.result import AsyncResult
    from tasks.worker_celery import run_interview_analysis_task, generate_report_task, celery_app
    CELERY_AVAILABLE = True
    logger.info("✅ Celery importé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur import Celery: {e}")
    CELERY_AVAILABLE = False
    celery_app = None

class AnalysisRequest(BaseModel):
    conversation_history: List[Dict[str, Any]]
    job_description_text: str
    candidate_id: Optional[str] = None

class ReportRequest(BaseModel):
    analysis_data: Dict[str, Any]
    candidate_id: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None
    progress: Optional[str] = None

@app.post("/trigger-analysis", response_model=TaskResponse, status_code=202)
async def trigger_analysis(request: AnalysisRequest):
    """
    Endpoint appelé par l'API ML pour déclencher une analyse en arrière-plan.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Service Celery indisponible - worker non démarré"
        )
    
    logger.info(f"Déclenchement d'analyse pour candidat: {request.candidate_id}")
    
    try:
        task = run_interview_analysis_task.delay(
            request.conversation_history, 
            [request.job_description_text]
        )
        
        return {
            "task_id": task.id, 
            "status": "PENDING", 
            "result": None,
            "progress": "Analyse démarrée"
        }
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement de l'analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-report", response_model=TaskResponse, status_code=202)
async def trigger_report(request: ReportRequest):
    """
    Endpoint pour déclencher la génération d'un rapport.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Service Celery indisponible - worker non démarré"
        )
    
    logger.info(f"Déclenchement de génération de rapport pour: {request.candidate_id}")
    
    try:
        task = generate_report_task.delay(request.analysis_data)
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "result": None,
            "progress": "Génération de rapport démarrée"
        }
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement du rapport: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task-status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Endpoint appelé par l'API ML pour vérifier le statut d'une tâche.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Service Celery indisponible - worker non démarré"
        )
    
    logger.info(f"Vérification du statut pour la tâche: {task_id}")
    
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Déterminer le message de progression
        progress_msg = None
        if task_result.status == "PENDING":
            progress_msg = "En attente de traitement"
        elif task_result.status == "STARTED":
            progress_msg = "Traitement en cours"
        elif task_result.status == "SUCCESS":
            progress_msg = "Traitement terminé"
        elif task_result.status == "FAILURE":
            progress_msg = "Erreur lors du traitement"
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result,
            "progress": progress_msg
        }
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Annuler une tâche en cours.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Service Celery indisponible - worker non démarré"
        )
    
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"message": f"Tâche {task_id} annulée"}
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def health_check():
    """Health check de l'API Celery."""
    return {
        "status": "ok",
        "service": "AIrh Celery Worker",
        "celery_available": CELERY_AVAILABLE,
        "message": "API FastAPI fonctionnelle" + (" - Celery OK" if CELERY_AVAILABLE else " - Celery KO")
    }

@app.get("/worker-stats")
async def worker_stats():
    """Statistiques des workers Celery."""
    if not CELERY_AVAILABLE:
        return {
            "error": "Celery non disponible",
            "celery_available": False
        }
    
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()
        
        return {
            "stats": stats,
            "active_tasks": active,
            "registered_tasks": registered,
            "celery_available": True
        }
    except Exception as e:
        return {
            "error": f"Impossible d'obtenir les stats: {e}",
            "celery_available": False
        }
