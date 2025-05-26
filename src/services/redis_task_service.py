from src.configs.redis_config import get_redis_client  # 导入统一配置
import logging

logger = logging.getLogger("celery")

class RedisTaskService:
    @staticmethod
    def scan_ocr_tasks(match_pattern: str = "vlm_ocr_*"):
        """扫描待处理的OCR任务键（使用统一 Redis 客户端）"""
        redis_generator = get_redis_client()  # 获取生成器
        redis_client = next(redis_generator)  # 提取客户端
        try:
            cursor = '0'
            tasks = []
            while True:
                cursor, keys = redis_client.scan(cursor, match=match_pattern, count=100)
                if keys:
                    tasks.extend(keys)
                if cursor == 0:
                    break
            return tasks
        finally:
            next(redis_generator, None)  # 执行生成器清理逻辑（归还连接）

    @staticmethod
    def delete_task_key(task_key: str):
        """删除已处理的任务键（使用统一 Redis 客户端）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            redis_client.delete(task_key)
            logger.info(f"清理任务键: {task_key}")
        finally:
            next(redis_generator, None)

    @staticmethod
    def get_and_delete_task_data(task_key: str):
        """获取并删除任务键的数据（使用统一 Redis 客户端）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            data = redis_client.getdel(task_key)  # 原子操作：获取并删除键
            logger.info(f"获取并删除任务数据: {task_key}")
            return data
        finally:
            next(redis_generator, None)