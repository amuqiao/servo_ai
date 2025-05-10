import os
import pytz
from datetime import datetime
import logging
import tempfile
from logging.handlers import RotatingFileHandler
from typing import Optional
from src.configs import ApiConfig

def setup_logging() -> Optional[logging.Logger]:
    """
    配置符合FastAPI规范的日志系统
    包含文件滚动记录和控制台输出，日志格式符合RESTful规范
    """

    config = ApiConfig()
    log_level = config.LOG_LEVEL.upper()
    log_dir = config.LOG_DIR

    # 打印日志目录路径，用于调试
    print(f"log_level: {log_level}")  # 打印日志级别，用于调试
    print(f"log_dir: {log_dir}")  # 打印日志目录，用于调试
    
    # 尝试创建日志目录，失败则使用临时目录
    try:
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError:
        log_dir = os.path.join('/tmp', 'servoai_logs')
        os.makedirs(log_dir, exist_ok=True)
        logging.warning(f"Using temporary log directory: {log_dir}")
    log_format = config.LOG_FORMAT or (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    date_format = config.LOG_DATE_FORMAT or (
        "%Y-%m-%d %H:%M:%S"
    )
    timezone = pytz.timezone(config.LOG_TIMEZONE or "Asia/Shanghai")

    class ShanghaiTimeFormatter(logging.Formatter):
        def converter(self, timestamp):
            return datetime.fromtimestamp(timestamp, timezone).timetuple()
    
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 初始化根日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有处理器避免重复
    if logger.handlers:
        logger.handlers.clear()

    try:
        # 文件处理器（带滚动）
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "servoai-api.log"),
            maxBytes=int(config.LOG_FILE_MAX_SIZE) * 1024 * 1024,  # 默认10MB
            backupCount=int(config.LOG_FILE_BACKUP_COUNT)  # 默认保留5个备份
        )
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 设置第三方库日志级别
        logging.getLogger("uvicorn.access").handlers = logger.handlers
        logging.getLogger("uvicorn").setLevel(log_level)
        
        return logger
    except Exception as e:
        print(f"日志初始化失败: {str(e)}")
        return None