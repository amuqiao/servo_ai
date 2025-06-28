from fastapi import HTTPException
from enum import Enum
from .common_exceptions import CommonErrorCode
from typing import Dict, Any, Optional

class WorkOrderErrorCode(Enum):
    # 工单业务错误码（遵循500xx系列）
    WORK_ORDER_SUBMIT_FAILED = 50010  # 工单提交失败
    WORK_ORDER_VALIDATE_FAILED = 40010  # 工单验证失败
    WORK_ORDER_NOT_FOUND = 40410  # 工单不存在

class WorkOrderException(HTTPException):
    def __init__(
        self,
        code: CommonErrorCode | WorkOrderErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None):
        status_code = code.value // 100
        super().__init__(status_code=status_code, detail=message)
        self.code = code.value
        self.message = message
        self.details = details