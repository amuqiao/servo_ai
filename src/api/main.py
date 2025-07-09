from fastapi import FastAPI
from src.routers import router
from src.routers import health_check, task_router, vlm_ocr_router, user_router, power_plant, work_order_router, celery_demo_router, taxpayer_cert_router
from src.routers.ocr import ocr_record_router, ocr_task_router
from src.routers import timeseries_router
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging, LogConfig
from src.celery_app import app as celery_app
from src.middlewares.exception_handler import add_exception_handlers

import sys
import os
import logging


# 获取特定模块的日志器
logger = logging.getLogger(__name__)
config = ApiConfig()

app = FastAPI(title="ServoAI_API", version="1.0.0")

# 添加异常处理器
add_exception_handlers(app)

# 配置日志
config = LogConfig(LOGGING_LEVEL=logging.INFO)
setup_logging(app)

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
app.include_router(timeseries_router.router)
app.include_router(taxpayer_cert_router.router)


@app.get("/")
async def root():
    return "Hello world2"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
