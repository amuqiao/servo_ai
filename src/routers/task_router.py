from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


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
