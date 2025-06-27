from fastapi import FastAPI
from src.routers import router
from src.routers import health_check, task_router, vlm_ocr_router, user_router, power_plant,work_order_router,celery_demo_router
from src.routers.ocr import ocr_record_router, ocr_task_router
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging, LogConfig
from src.celery_app import app as celery_app

import sys
import os
import logging


# 获取特定模块的日志器
logger = logging.getLogger(__name__)
config = ApiConfig()

app = FastAPI(title="ServoAI_API", version="1.0.0")

# 配置日志
config = LogConfig(LOGGING_LEVEL=logging.INFO)
setup_logging(app)

# 注册路由模块 todo 这里为什么要注册router呢？
app.include_router(router)

# 注册所有路由
app.include_router(health_check.router)
app.include_router(task_router.router)
app.include_router(ocr_record_router.router)
app.include_router(ocr_task_router.router)
app.include_router(vlm_ocr_router.router)
# app.include_router(user_router.router)
app.include_router(power_plant.router)
app.include_router(work_order_router.router)
app.include_router(celery_demo_router.router)

# 初始化Celery配置
# @app.on_event('startup')
# async def init_celery():
#     logger.info("正在初始化Celery配置...")
#     try:
#         config_params = {
#             "broker": ApiConfig().CELERY_BROKER_URL[:25] + '*****',
#             "backend": ApiConfig().CELERY_RESULT_BACKEND[:20] + '*****',
#             "task_serializer": 'json',
#             "result_expires": 3600
#         }
#         logger.debug(f"Celery配置参数: {config_params}")

#         celery_app.conf.update(
#             broker_url=ApiConfig().CELERY_BROKER_URL,
#             backend=ApiConfig().CELERY_RESULT_BACKEND,
#             task_serializer='json',
#             accept_content=['json'],
#             result_serializer='json',
#             beat_schedule=beat_schedule,
#             result_expires=3600,
#         )
#         logger.info("Celery配置成功")
#     except Exception as e:
#         logger.error("Celery初始化失败", exc_info=True)
#         raise


@app.get("/")
async def root():
    return "Hello world2"

if __name__ == "__main__":
    import uvicorn
    # import sys, os
    # print(f"当前工作目录：{os.getcwd()}")
    # print(f"Python路径：{sys.path}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
