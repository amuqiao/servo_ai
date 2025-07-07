from pydantic import BaseModel, Field
from typing import List, Dict, Any
from .response_schema import SuccessResponse

class OnTheWayWorkOrder(BaseModel):
    id: str
    taskId: str
    powerName: str
    powerNumber: str
    startTime: str
    taskStatus: int
    orderAdvice: str
    repeatRate: float = Field(None, example=0.5)

class WorkOrderResult(BaseModel):
    """工单处理结果模型"""
    content: str
    repeatRate: float
    onTheWayWorkOrderList: List[OnTheWayWorkOrder]

class WorkOrderRequest(BaseModel):
    repeatRate: float = Field(None, example=0.5)  # 修改为非必填项
    content: str = Field(..., example="设备故障")
    onTheWayWorkOrderList: List[OnTheWayWorkOrder] = Field(..., min_items=1, example=[
        {
            "id": "12345",
            "taskId": "T001",
            "powerName": "电站A",
            "powerNumber": "P001",
            "startTime": "2025-06-06 14:35:00",
            "taskStatus": 0,
            "orderAdvice": "请检查设备运行状态",
        },
        {
            "id": "67890",
            "taskId": "T002",
            "powerName": "电站B",
            "powerNumber": "P002",
            "startTime": "2025-06-06 15:00:00",
            "taskStatus": 1,
            "orderAdvice": "请维护电站设备"
        }
    ])

class WorkOrderResponse(SuccessResponse):
    """工单提交响应模型"""
    data: WorkOrderResult | None = None