import os
import pytz
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def setup_logging() -> Optional[logging.Logger]:
    """
    配置符合FastAPI规范的日志系统
    包含文件滚动记录和控制台输出，日志格式符合RESTful规范
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "/app/api/logs")
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s")
    date_format = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
    timezone = pytz.timezone(os.getenv("LOG_TZ", "Asia/Shanghai"))

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
            maxBytes=int(os.getenv("LOG_FILE_MAX_SIZE", 10)) * 1024 * 1024,  # 默认10MB
            backupCount=int(os.getenv("LOG_FILE_BACKUP_COUNT", 5))
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