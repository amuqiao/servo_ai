from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/api/work-order", tags=["工单接口"])

class OnTheWayWorkOrder(BaseModel):
    id: str
    taskId: str
    powerName: str
    powerNumber: str
    startTime: str
    taskStatus: int
    orderAdvice: str

class WorkOrderRequest(BaseModel):
    repeatRate: str = Field(..., example="50%")
    content: str = Field(..., example="工单内容示例")
    onTheWayWorkOrderList: List[OnTheWayWorkOrder] = Field(..., min_items=2, example=[
        {
            "id": "12345",
            "taskId": "T001",
            "powerName": "电站A",
            "powerNumber": "P001",
            "startTime": "2025-06-06 14:35:00",
            "taskStatus": 0,
            "orderAdvice": "请检查设备运行状态"
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

@router.post("/submit", response_model=WorkOrderRequest)
async def submit_work_order(work_order: WorkOrderRequest):
    """提交工单接口，返回接收的请求体"""
    return work_order