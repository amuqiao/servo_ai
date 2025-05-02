import logging
import os
from logging.handlers import RotatingFileHandler
from src.configs import ApiConfig

config = ApiConfig()

LOG_DIR = os.path.join(config.ROOT_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# 创建根logger
def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # 文件处理器（按大小轮转）
    file_handler = RotatingFileHandler(
        filename=os.path.join(LOG_DIR, 'api.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)