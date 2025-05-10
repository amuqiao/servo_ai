from fastapi import Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging
from urllib.parse import quote_plus
from sqlalchemy.engine import URL
import logging

setup_logging()
logger = logging.getLogger(__name__)

Base = declarative_base()

def get_db_engine():
    """创建带连接池配置的数据库引擎"""
    config = ApiConfig()
    try:
        connection_dict = {
            "drivername": "mysql+pymysql",
            "username": config.DB_USER,
            "password": quote_plus(config.DB_PASSWORD),
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "database": config.DB_NAME
        }
        
        # 添加连接池配置
        pool_config = {
            "pool_size": 10,          # 连接池保持的连接数
            "max_overflow": 5,        # 允许临时增加的连接数
            "pool_timeout": 30,       # 获取连接的超时时间（秒）
            "pool_recycle": 3600      # 连接重置周期（秒）
        }
        
        connection_url = URL.create(**connection_dict)
        return create_engine(
            connection_url, 
            pool_pre_ping=True,
            **pool_config
        )
    except Exception as e:
        logger.error(f"数据库引擎创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库引擎初始化失败")

# 使用工厂模式创建会话本地类
SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_db_engine(),
    class_=Session  # 显式指定会话类
)

def get_db_conn() -> Session:
    """依赖注入用的数据库会话生成器"""
    db = SessionFactory()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="数据库操作失败")
    finally:
        db.close()