import os
import logging
from logging.handlers import RotatingFileHandler
from pydantic_settings import BaseSettings
from fastapi import FastAPI
from typing import Optional

class LogConfig(BaseSettings):
    """日志配置类"""
    LOGGING_LEVEL: int = logging.INFO  # 默认日志级别
    LOG_DIR: str = "logs"  # 日志文件存储目录
    LOG_FILE_MAX_SIZE: int = 10 * 1024 * 1024  # 单个日志文件最大大小 (10MB)
    LOG_FILE_BACKUP_COUNT: int = 5  # 日志文件备份数量
    LOG_FORMAT: str = "%(asctime)s %(levelname)-2s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"  # 日志格式

def setup_logging(app: Optional[FastAPI] = None, config: Optional[LogConfig] = None) -> None:
    """
    设置 FastAPI 应用的日志系统
    
    Args:
        app: FastAPI 应用实例，如果提供则为其设置日志
        config: 日志配置对象
    """
    # 如果未提供配置，使用默认配置
    if config is None:
        config = LogConfig()
     
    # 创建日志目录（如果不存在）
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # 设置日志格式
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 创建文件处理器（按大小分割）
    file_handler = RotatingFileHandler(
        os.path.join(config.LOG_DIR, "app.log"),
        maxBytes=config.LOG_FILE_MAX_SIZE,
        backupCount=config.LOG_FILE_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # 移除默认处理器
    root_logger.setLevel(config.LOGGING_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 配置 FastAPI 特定日志器
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(file_handler)
    uvicorn_access_logger.setLevel(config.LOGGING_LEVEL)
    
    # 如果提供了 FastAPI 应用实例，添加启动和关闭事件
    if app:
        @app.on_event("startup")
        def startup_logging() -> None:
            logging.info("FastAPI 应用启动成功")
        
        @app.on_event("shutdown")
        def shutdown_logging() -> None:
            logging.info("FastAPI 应用优雅关闭")

def setup_celery_logging(config: Optional[LogConfig] = None) -> None:
    """
    设置Celery的日志系统
    
    Args:
        config: 日志配置对象
    """
    # 如果未提供配置，使用默认配置
    if config is None:
        config = LogConfig()
     
    # 创建日志目录（如果不存在）
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # 设置日志格式
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # 创建文件处理器（按大小分割）
    celery_file_handler = RotatingFileHandler(
        os.path.join(config.LOG_DIR, "celery.log"),
        maxBytes=config.LOG_FILE_MAX_SIZE,
        backupCount=config.LOG_FILE_BACKUP_COUNT
    )
    celery_file_handler.setFormatter(formatter)
    
    # 配置Celery根日志器
    celery_logger = logging.getLogger("celery")
    celery_logger.handlers.clear()  # 移除默认处理器
    celery_logger.addHandler(celery_file_handler)
    celery_logger.setLevel(config.LOGGING_LEVEL)
    celery_logger.propagate = False  # 防止日志向上传播到根日志器
    
    # 配置Celery任务日志器
    task_logger = logging.getLogger("celery.task")
    task_logger.handlers.clear()
    task_logger.addHandler(celery_file_handler)
    task_logger.setLevel(config.LOGGING_LEVEL)
    task_logger.propagate = False
    
    # 配置Celery工作进程日志器
    worker_logger = logging.getLogger("celery.worker")
    worker_logger.handlers.clear()
    worker_logger.addHandler(celery_file_handler)
    worker_logger.setLevel(config.LOGGING_LEVEL)
    worker_logger.propagate = False
    
    # 配置Celery Beat日志器
    beat_logger = logging.getLogger("celery.beat")
    beat_logger.handlers.clear()
    beat_logger.addHandler(celery_file_handler)
    beat_logger.setLevel(config.LOGGING_LEVEL)
    beat_logger.propagate = False

# 使用示例
if __name__ == "__main__":
    # 测试日志配置
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("测试日志输出")
