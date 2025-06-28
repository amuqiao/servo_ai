from fastapi import APIRouter
from src.schemas.work_order_schemas import WorkOrderRequest, WorkOrderResponse
from src.services.work_order_service import WorkOrderService  # 新增服务导入

router = APIRouter(prefix="/api/work-order", tags=["工单接口"])

@router.post("/submit", response_model=WorkOrderResponse)
async def submit_work_order(work_order: WorkOrderRequest):
    """提交工单接口（路由层仅处理请求转发）"""
    # 调用服务层处理业务逻辑
    processed_order = WorkOrderService.submit_work_order(work_order)
    return WorkOrderResponse(data=processed_order)