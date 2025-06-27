from pydantic import BaseModel, Field
from typing import List

class DemoTaskRequest(BaseModel):
    task_data: dict = Field(
        ...,
        example={
                "content": {
                    "urls": [
                        " https://xuntian-pv.tcl.com/group1/M00/2C/72/rBAAOGdzuwGATMSIAAJAsZYWXKI601.pdf ",
                        " https://xuntian-pv.tcl.com/group1/M00/2C/64/rBAAOGdzkjmAeKrxAAJAsZYWXKI702.pdf ",
                        " https://xuntian-pv.tcl.com/group1/M00/1A/19/rBAAOGchjDeAZli9AAFfY8v0R18553.jpg "
                    ]
                },
                "task_id": "123",
                "task_type": "ocr_cert_processing"
        },
        description="单个任务数据（必须包含task_type字段标识任务类型，直接接收 Python 字典，长度通过序列化后字符串控制在 1-1024 字符）"
    )  # 直接接受 Python 字典输入

class GenerateTasksRequest(BaseModel):
    count: int = Field(
        ...,
        gt=0, lt=2000, # 限制1-100个任务
        example=5,
        description="需要生成的任务数量（1-100之间的整数）"
    )
    task_type: str = Field(
        ...,
        min_length=1,
        example="data_processing",
        description="生成任务的统一类型标识（如：data_processing、data_analysis等）"
    )

class BatchDemoTaskRequest(BaseModel):
    task_data_list: List[dict] = Field(
        ...,
        min_items=1, # 至少1个任务
        max_items=100, # 限制最大100个任务
        example=[
            {"task_type": "data_processing", "task_id": "1", "content": "批量内容1"},
            {"task_type": "data_processing", "task_id": "2", "content": "批量内容2"}
        ],
        description="批量任务数据列表（每个元素为包含task_type字段的任务数据字典，直接接收 Python 字典列表，最多 100 个，需与DemoTaskRequest的task_data结构一致）"
    )  # 每个元素为与DemoTaskRequest.task_data兼容的字典