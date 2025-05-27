from src.configs.redis_config import get_redis_client  # 导入统一配置
from src.models import OCRModel
import logging
import uuid
import json

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

    @staticmethod
    async def store_task_data(data: dict) -> str:
        """
        公共方法：将任务数据存储到Redis并生成唯一任务ID
        :param data: 任务数据（格式：{record_id: [url1, url2, ...]}）
        :return: 生成的Redis任务ID（格式：vlm_ocr_+UUID）
        """
        try:
            task_id = f"vlm_ocr_{uuid.uuid4()}"
            logger.debug(f"生成Redis任务ID：{task_id}，数据：{data}")

            redis_generator = get_redis_client()
            redis_client = next(redis_generator)
            redis_client.set(task_id, json.dumps(data))
            logger.info(f"Redis存储成功，任务ID：{task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Redis存储失败，任务数据：{data}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="缓存服务异常")
        finally:
            next(redis_generator, None)

    @staticmethod
    async def process_records_to_tasks(records: list[OCRModel]) -> list[str]:
        """
        公共方法：将OCR记录列表转换为Redis任务ID列表（从task_processor迁移）
        :param records: OCR记录列表
        :return: 生成的任务ID列表
        """
        task_ids = []
        for record in records:
            urls = record.url.split(',') if record.url else []
            task_data = {str(record.id): urls}
            task_id = await RedisTaskService.store_task_data(task_data)  # 调用自身存储方法
            task_ids.append(task_id)
            logger.debug(f"生成OCR任务，记录ID：{record.id}，任务ID：{task_id}")
        return task_ids