from fastapi import FastAPI
from routers import router
from src.routers import health_check, task_router, task_processor, vlm_ocr_router, user_router
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging
from src.celery_app import app as celery_app
from src.configs.celery_config import beat_schedule

setup_logging()

app = FastAPI(title="ServoAI_API", version="1.0.0")

# 注册路由模块 todo 这里为什么要注册router呢？
app.include_router(router)

# 注册所有路由
app.include_router(health_check.router)
app.include_router(task_router.router)
app.include_router(task_processor.router)
app.include_router(vlm_ocr_router.router)
app.include_router(user_router.router)

# 初始化Celery配置
@app.on_event('startup')
async def init_celery():
    
    celery_app.conf.update(
        broker_url=ApiConfig().CELERY_BROKER_URL,
        backend=ApiConfig().CELERY_RESULT_BACKEND,
        task_serializer='json',
        accept_content=['json'], # todo 这里为什么要加这个呢？
        result_serializer='json',
        beat_schedule=beat_schedule,
        result_expires=3600,
    )
    
@app.get("/")
async def root():
    return "Hello world2"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)