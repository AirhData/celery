import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from celery.result import AsyncResult
from dotenv import load_dotenv

# Import de la tâche Celery
from tasks.worker_celery import run_interview_analysis_task, celery_app

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIrh Celery Worker Service",
    description="Service dédié à l'exécution des tâches d'analyse IA.",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    conversation_history: List[Dict[str, Any]]
    job_description_text: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None

@app.post("/trigger-analysis", response_model=TaskResponse, status_code=202)
async def trigger_analysis(request: AnalysisRequest):
    """Déclenche une tâche d'analyse en arrière-plan."""
    logger.info("Requête reçue pour déclencher une analyse.")
    task = run_interview_analysis_task.delay(request.conversation_history, [request.job_description_text])
    return {"task_id": task.id, "status": "PENDING", "result": None}

@app.get("/analysis-status/{task_id}", response_model=TaskResponse)
async def get_analysis_status(task_id: str):
    """Vérifie le statut d'une tâche d'analyse."""
    logger.info(f"Vérification du statut pour la tâche: {task_id}")
    task_result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status, "result": task_result.result}

@app.get("/")
async def health_check():
    """Vérifie que le service est en ligne."""
    return {"status": "ok"}
