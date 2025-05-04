from routers import router
from fastapi import FastAPI
from src.routers import health_check, task_router, task_processor, vlm_ocr_router
from src.celery_app import app as celery_app
from src.configs import ApiConfig
# from dotenv import load_dotenv
# load_dotenv()


# app = FastAPI()
app = FastAPI(title="ServoAI_API", version="1.0.0")

# 注册路由模块
app.include_router(router)

# 路由注册
# 原注册方式（已移除prefix）
app.include_router(health_check.router)
app.include_router(task_router.router)

# 在路由注册部分添加
app.include_router(task_processor.router)
app.include_router(vlm_ocr_router.router)
# app.include_router(user_router.router)

# 初始化Celery应用
@app.on_event('startup')
async def celery_init():
    from src.configs.celery_config import beat_schedule
    
    celery_app.conf.update(
        broker_url=ApiConfig().CELERY_BROKER_URL,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        beat_schedule=beat_schedule
    )


@app.get("/")
async def root():
    return "Hello world2"

if __name__ == "__main__":
    pass
