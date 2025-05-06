from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

Base = declarative_base()

from urllib.parse import quote_plus
from sqlalchemy.engine import URL

def get_db_engine():
    config = ApiConfig()
    try:
        # 使用字典配置参数
        connection_dict = {
            "drivername": "mysql+pymysql",
            "username": config.DB_USER,
            "password": quote_plus(config.DB_PASSWORD),  # URL编码处理特殊字符
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "database": config.DB_NAME
        }
        # 使用URL.create构建安全连接字符串
        connection_url = URL.create(**connection_dict)
        return create_engine(connection_url, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"数据库引擎创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库引擎初始化失败")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_db_engine())

def get_db_conn():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()