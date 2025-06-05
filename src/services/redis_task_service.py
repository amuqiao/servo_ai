from src.configs.redis_config import get_redis_client  # 导入统一配置
from src.models import OCRModel
import logging
import uuid
import json

logger = logging.getLogger("celery")

class RedisTaskService:
    @staticmethod
    def scan_ocr_tasks(match_pattern: str = "vlm_ocr_*", max_count: int = 1000):
        """扫描待处理的OCR任务键（支持批量限制）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            cursor = '0'
            tasks = []
            while True:
                cursor, keys = redis_client.scan(cursor, match=match_pattern, count=10)
                if keys:
                    remaining = max_count - len(tasks)
                    tasks.extend(keys[:remaining])
                    if len(tasks) >= max_count:
                        break
                if cursor == 0:
                    break
            logger.debug(f"扫描到{len(tasks)}个OCR任务键（模式：{match_pattern}）")  # 保留debug（非关键流程）
            return tasks
        finally:
            next(redis_generator, None)

    @staticmethod
    def delete_task_key(task_key: str):
        """删除已处理的任务键（使用统一 Redis 客户端）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            redis_client.delete(task_key)
            logger.debug(f"清理任务键: {task_key}")  # 保留debug（非关键流程）
        finally:
            next(redis_generator, None)

    @staticmethod
    def get_and_delete_task_data(task_key: str):
        """获取并删除任务键的数据（使用统一 Redis 客户端）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            data = redis_client.getdel(task_key)
            logger.debug(f"获取并删除任务数据: {task_key}")  # 保留debug（非关键流程）
            return data
        finally:
            next(redis_generator, None)

    @staticmethod
    async def store_task_data(record_id: int, business_id: str, data: dict) -> str:  # 修改参数，新增 record_id 和 business_id
        """公共方法：将任务数据存储到Redis并生成唯一任务ID"""
        try:
            task_id = f"vlm_ocr_{record_id}_{business_id}"  # 使用 id 和 business_id 生成任务ID
            logger.debug(f"生成Redis任务ID：{task_id}，数据：{data}")
            redis_generator = get_redis_client()
            redis_client = next(redis_generator)
            redis_client.set(task_id, json.dumps(data))
            logger.debug(f"Redis存储成功：{task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Redis存储失败（数据：{data}）：{str(e)}", exc_info=True)
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
            # 新增：跳过ai_status=1的已处理记录
            if record.ai_status == 1:
                logger.debug(f"跳过ai_status=1的记录（无需重复创建任务），记录ID：{record.id}")
                continue
            urls = record.url.split(',') if record.url else []
            task_data = {str(record.id): urls}
            # 调用 store_task_data 时传递当前记录的 id 和 business_id
            task_id = await RedisTaskService.store_task_data(record.id, record.business_id, task_data)  # 修改调用参数
            task_ids.append(task_id)
            logger.debug(f"生成OCR任务，记录ID：{record.id}，任务ID：{task_id}")
        return task_ids

    @staticmethod
    def check_task_exists(task_key: str) -> bool:
        """检查任务键是否存在（防止并发冲突）"""
        redis_generator = get_redis_client()
        redis_client = next(redis_generator)
        try:
            return redis_client.exists(task_key) == 1
        finally:
            next(redis_generator, None)