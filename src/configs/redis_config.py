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
            # 新增：显式配置连接池参数（根据业务需求调整）
            _redis_pool = ConnectionPool(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
                max_connections=100,  # 高并发场景建议调大（默认10）
                socket_timeout=5,  # 连接超时时间（秒）
                retry_on_timeout=True,  # 超时重试
            )
            logger.debug(
                f"Redis 连接池初始化成功（host={config.redis.host}:{config.redis.port}，max_connections=100）"
            )
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
        # 优化：区分连接错误与操作错误
        if isinstance(e, (ConnectionError, TimeoutError)):
            logger.error(f"Redis 连接异常: {str(e)}")
            raise HTTPException(status_code=503, detail="Redis 服务不可用")
        else:
            logger.error(f"Redis 操作异常: {str(e)}")
            raise HTTPException(status_code=500, detail="Redis 操作失败")
    finally:
        client.close()  # 归还连接到池（非真正关闭）
