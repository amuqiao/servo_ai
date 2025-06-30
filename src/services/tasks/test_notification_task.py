import logging
from typing import Dict, Any
from .base_task import BaseTask

# 初始化任务专用日志器
logger = logging.getLogger("celery")

class TestNotificationTask(BaseTask):
    task_type = "test_notification"

    def __init__(self, task_id: str, content: Dict[str, Any]):
        super().__init__(task_id, content)

    def parse_content(self) -> Dict[str, Any]:
        # 解析逻辑实现
        return self.content
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestNotificationTask':
        return cls(
            task_id=data["task_id"],
            content=data["content"]
        )

    def process(self) -> Dict[str, Any]:
        # 添加任务处理日志
        logger.info(f"开始处理通知任务，ID: {self.task_id}，内容: {self.content}")
        
        # 实际业务处理逻辑
        processed_result = {"status": "notified", "content": self.content}
        
        # 添加处理结果日志
        logger.info(f"通知任务处理完成，ID: {self.task_id}")
        
        return {
            "status": "success",
            "task_id": self.task_id,
            "result": processed_result
        }
