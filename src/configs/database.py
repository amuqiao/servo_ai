from fastapi import Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.configs import ApiConfig
from src.configs.logging_config import setup_logging
from urllib.parse import quote_plus
from sqlalchemy.engine import URL
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_db_engine():
    """创建带连接池配置的数据库引擎"""
    config = ApiConfig()
    try:
        # 改为从database子配置获取值
        connection_dict = {
            "drivername": "mysql+pymysql",
            "username": config.database.user,  # 原config.DB_USER → config.database.user
            "password": quote_plus(config.database.password),  # 原config.DB_PASSWORD → config.database.password
            "host": config.database.host,  # 原config.DB_HOST → config.database.host
            "port": config.database.port,  # 原config.DB_PORT → config.database.port
            "database": config.database.db_name  # 原config.DB_NAME → config.database.db_name
        }
        
        logger.info(
            "正在初始化数据库连接，驱动：%s,主机：%s, 端口：%s, 数据库：%s, 用户：%s",
            connection_dict["drivername"],
            connection_dict["host"],
            connection_dict["port"],
            connection_dict["database"],
            connection_dict["username"]
        )

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
            echo=False,
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
