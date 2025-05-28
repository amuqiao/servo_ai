from fastapi import HTTPException
from redis import Redis, ConnectionPool
from src.configs import ApiConfig
import logging

logger = logging.getLogger(__name__)

# 全局连接池（单例模式）
_redis_pool = None

def get_redis_pool() -> ConnectionPool:
    """获取 Redis 连接池（单例）"""
    global _redis_pool
    if _redis_pool is None:
        config = ApiConfig()
        try:
            _redis_pool = ConnectionPool(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                password=config.REDIS_PASSWORD,
                db=config.REDIS_DB,
                decode_responses=True  # 自动解码为字符串
            )
            logger.debug(f"Redis 连接池初始化成功（host={config.REDIS_HOST}:{config.REDIS_PORT}）")
        except Exception as e:
            logger.error(f"Redis 连接池创建失败: {str(e)}")
            raise HTTPException(status_code=500, detail="Redis 连接池初始化失败")
    return _redis_pool

def get_redis_client() -> Redis:
    """依赖注入用的 Redis 客户端生成器（支持上下文管理器）"""
    pool = get_redis_pool()
    client = Redis(connection_pool=pool)
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis 客户端异常: {str(e)}")
        raise HTTPException(status_code=500, detail="Redis 操作失败")
    finally:
        client.close()  # 归还连接到池（非真正关闭）