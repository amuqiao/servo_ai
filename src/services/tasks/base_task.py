from abc import ABC, abstractmethod
import json
import logging
from typing import Dict, Any

# 初始化日志器（与subscriber_tasks.py保持一致）
logger = logging.getLogger("celery")

class BaseTask(ABC):
    task_type: str = None

    @abstractmethod
    def __init__(self, task_id: str, content: Any):
        self.task_id = task_id
        self.content = content

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseTask':
        """从字典数据解析任务对象"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典用于Redis发布"""
        return {
            "task_type": self.task_type,
            "task_id": self.task_id,
            "content": self.content
        }

    @abstractmethod
    def process(self) -> Dict[str, Any]:
        """任务处理逻辑"""
        pass


class DataProcessingTask(BaseTask):
    task_type = "data_processing"

    def __init__(self, task_id: str, content: str):
        super().__init__(task_id, content)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataProcessingTask':
        return cls(
            task_id=data["task_id"],
            content=data["content"]
        )

    def process(self) -> Dict[str, Any]:
        # 添加任务处理日志
        logger.info(f"开始处理数据任务，ID: {self.task_id}，内容: {repr(self.content)}") 
        
        # 实际业务处理逻辑
        processed_result = self.content  # 直接使用字典内容或实现正确的业务逻辑
        
        # 添加处理结果日志
        logger.info(f"数据任务处理完成，ID: {self.task_id}，结果长度: {len(processed_result)}")
        
        return {
            "status": "success",
            "task_id": self.task_id,
            "result": processed_result
        }