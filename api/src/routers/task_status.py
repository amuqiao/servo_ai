from fastapi import APIRouter, HTTPException
from celery_app import app as celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    
    if not task.ready():
        return {"status": "PENDING"}
        
    if task.successful():
        return {"status": "SUCCESS", "result": task.result}
    
    if task.failed():
        return {"status": "FAILURE", "error": str(task.result)}