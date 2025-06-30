from fastapi import APIRouter
from src.schemas.work_order_schemas import WorkOrderRequest, WorkOrderResponse
from src.services.work_order_service import WorkOrderService

router = APIRouter(prefix="/api/work-order", tags=["工单接口"])

@router.post("/submit", response_model=WorkOrderResponse)
async def submit_work_order(work_order: WorkOrderRequest):
    """提交工单接口（异步版本）"""
    # 异步调用服务层方法
    processed_order = await WorkOrderService.submit_work_order(work_order)
    return WorkOrderResponse(data=processed_order)