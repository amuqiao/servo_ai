from pydantic import BaseModel
from typing import List
from src.schemas.response_schema import BaseResponse  # 导入统一响应体

# 基础任务数据模型（整合所有可能字段）
class OCRTaskData(BaseModel):
    """OCR任务数据模型（整合基础/业务/公司关联场景）"""
    task_ids: List[str]  # 必选：任务ID列表
    count: int  # 必选：任务数量
    business_ids: List[str]  # 必选：业务ID列表（电站编号）
    company_ids: List[str]  # 必选：公司ID列表

# 统一响应模型（替代原多个子类响应）
class OCRTaskResponse(BaseResponse):
    """OCR任务统一响应模型"""
    data: OCRTaskData | None = None

# 任务创建请求模型（保持简洁参数校验）
class CreateTasksRequest(BaseModel):
    """OCR任务创建请求模型"""
    ids: List[str]  # 通用ID列表（业务ID/公司ID）
    type: str = "business"  # 可选："business"（业务ID）或"company"（公司ID）