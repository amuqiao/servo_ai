from fastapi import APIRouter, HTTPException
from src.celery_app.tasks import create_redis_key_task, create_redis_key_task2
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

class TaskResponse(BaseModel):
    task_id: str
    expires_in: int

@router.post("/delay-set", response_model=TaskResponse)
async def create_delayed_task():
    task_id = str(uuid.uuid4())
    task = create_redis_key_task.apply_async(args=[task_id], countdown=10)
    return {"task_id": task_id, "expires_in": 3600}

@router.post("/delay-set2", response_model=TaskResponse)
async def create_delayed_task2():
    task_id = str(uuid.uuid4())
    task = create_redis_key_task2(task_id=task_id)
    return {"task_id": task_id, "expires_in": 3600}

@router.get("/status/{redis_key}")
async def get_redis_status(redis_key: str):
    from src.configs import ApiConfig
    from urllib.parse import urlparse
    import redis
    
    redis_url = urlparse(ApiConfig().CELERY_BROKER_URL)
    client = redis.Redis(
        host=redis_url.hostname,
        port=redis_url.port,
        password=redis_url.password,
        db=redis_url.path.strip('/')
    )
    
    value = client.get(redis_key)
    ttl = client.ttl(redis_key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {
        "value": value.decode(),
        "ttl": ttl,
        "expire_human": f"{ttl // 3600} hours {ttl % 3600 // 60} minutes remaining" if ttl > 0 else "expired"
    }