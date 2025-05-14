import os
from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any
from src.configs.logging_config import setup_celery_logging, LogConfig


class CeleryConfig(BaseSettings):
    """Celery 配置类"""
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_RESULT_EXPIRES: int = 3600  # 结果保存时间（秒）
    CELERY_TIMEZONE: str = "Asia/Shanghai" # # 时间展示与转换：使用上海时区
    CELERY_ENABLE_UTC: bool = True # 内部时间存储与计算：使用 UTC

    # 定时任务配置
    CELERY_BEAT_SCHEDULE: Dict[str, Any] = {
        # 示例：每小时执行一次的任务
        "hourly-task": {
            "task": "src.celery_app.tasks.hourly_task",
            "schedule": 3600.0,  # 每小时执行
        },
    }

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",  # 从环境变量加载配置时的前缀
        env_file=".env",       # 环境变量文件
        env_file_encoding="utf-8",
        extra="ignore"         # 新增：忽略未定义的额外字段
    )


app = Celery(__name__)

# 创建配置实例
config = CeleryConfig()

# 创建日志配置实例
log_config = LogConfig()

# 设置Celery日志
setup_celery_logging(log_config)

app.conf.update(
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    task_serializer=config.CELERY_TASK_SERIALIZER,
    accept_content=config.CELERY_ACCEPT_CONTENT,
    result_serializer=config.CELERY_RESULT_SERIALIZER,
    result_expires=config.CELERY_RESULT_EXPIRES,
    timezone=config.CELERY_TIMEZONE,
    enable_utc=config.CELERY_ENABLE_UTC,
    beat_schedule=config.CELERY_BEAT_SCHEDULE,
    worker_hijack_root_logger=False,  # 避免 Celery 日志覆盖 FastAPI 日志
    worker_redirect_stdouts=False  # 避免 Celery 重定向到标准输出
)

app.autodiscover_tasks(packages=['src.celery_app'], related_name='tasks')
