import logging
from src.celery_app import app
from celery import shared_task
from datetime import datetime


@app.task
def test_task():
    return "Celery worker is functioning properly"


# 与CeleryConfig中CELERY_BEAT_SCHEDULE的task路径一致
@app.task(name="celery_app.test_tasks.hourly2_task")
def hourly2_task():
    logger = logging.getLogger("celery.task")  # 使用Celery任务日志器
    logger.info(f"定时任务 hourly_task2 执行，时间：{datetime.now().isoformat()}")
    return {"status": "success", "hourly2_task_message": "hourly2_task 执行完成"}
