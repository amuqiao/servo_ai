from . import app
from celery import shared_task
from src.configs import ApiConfig
from urllib.parse import urlparse
import redis
import time

@shared_task(name='celery_app.tasks.process_task')
def process_task():
    # 示例任务逻辑
    return {"result": "Task processed successfully"}

@shared_task(name='celery_app.tasks.create_redis_key_task')
def create_redis_key_task(task_id: str):
    redis_url = urlparse(ApiConfig().CELERY_BROKER_URL)
    
    client = redis.Redis(
        host=redis_url.hostname,
        port=redis_url.port,
        password=redis_url.password,
        db=int(redis_url.path.strip('/'))
    )
    
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    try:
        logger.info(f"[Task {task_id}] Connecting Redis: {redis_url.hostname}:{redis_url.port} DB: {redis_url.path}")
        client.ping()
        logger.info(f"[Task {task_id}] Storing key with TTL 3600s")
        client.setex(task_id, 3600, f"task_{task_id}_value_{time.time()}")
        logger.info(f"[Task {task_id}] Key stored successfully")
        return True
    except Exception as e:
        logger.error(f"[Task {task_id}] Redis operation failed: {str(e)}", exc_info=True)
        return False