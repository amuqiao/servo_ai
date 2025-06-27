import json
import uuid
import time  # 新增导入
from typing import Type, Dict, List, Any, Optional  # 添加Optional导入
from redis import Redis
from src.celery_app.app import CeleryConfig
from .tasks.base_task import BaseTask, DataProcessingTask
from .tasks.test_notification_task import TestNotificationTask
from .tasks.ocr_cert_task import OCRCertTask

# 任务注册表 - 核心扩展点
TASK_REGISTRY: Dict[str, Type[BaseTask]] = {
    DataProcessingTask.task_type: DataProcessingTask,
    TestNotificationTask.task_type: TestNotificationTask,
    OCRCertTask.task_type: OCRCertTask,
    # TestNotificationTask将在导入时自动注册到这里
}

class TaskService:
    @staticmethod
    def create_task(task_type: str, content: Any, task_id: Optional[str] = None) -> BaseTask:  # 新增task_id参数
        """创建任务实例，支持自定义task_id，默认生成uuid_时间戳格式"""
        if task_type not in TASK_REGISTRY:
            raise ValueError(f"不支持的任务类型: {task_type}")
        
        # 生成默认task_id：uuid4_时间戳
        if task_id is None:
            timestamp = int(time.time())
            task_id = f"{uuid.uuid4()}_{timestamp}"
        
        return TASK_REGISTRY[task_type](
            task_id=task_id,
            content=content
        )

    @staticmethod
    def publish_task(task: BaseTask, redis_client: Redis) -> None:
        """发布任务到Redis频道"""
        config = CeleryConfig()
        redis_client.publish(
            config.CELERY_TASK_QUEUE_CHANNEL,
            json.dumps(task.to_dict())
        )

    @staticmethod
    def publish_batch_tasks(tasks: List[BaseTask], redis_client: Redis) -> None:
        """批量发布任务"""
        config = CeleryConfig()
        for task in tasks:
            redis_client.publish(
                config.CELERY_TASK_QUEUE_CHANNEL,
                json.dumps(task.to_dict())
            )

    @staticmethod
    def parse_task(data: Dict[str, Any]) -> BaseTask:
        """从字典解析任务对象"""
        task_type = data.get("task_type")
        if not task_type or task_type not in TASK_REGISTRY:
            raise ValueError(f"无效的任务类型: {task_type}")
        return TASK_REGISTRY[task_type].from_dict(data)