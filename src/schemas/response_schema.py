from pydantic import BaseModel, Field
from typing import Any, Optional


class BaseResponse(BaseModel):
    code: int = 200  # 默认成功状态码
    message: str = "操作成功"  # 默认成功消息


class SuccessResponse(BaseResponse):
    data: Any = None  # 仅成功响应包含业务数据


class ErrorResponse(BaseResponse):
    code: int = Field(..., description="业务错误码")
    message: str = Field(..., description="错误信息")
    details: Optional[dict] = Field(None, description="错误详情")
    status_code: int = Field(..., description="HTTP状态码")
