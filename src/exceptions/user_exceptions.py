from enum import Enum
from fastapi import status, HTTPException
from .common_exceptions import CommonErrorCode  # 导入通用码
from typing import Dict, Any, Optional


class UserErrorCode(Enum):
    # 业务专属错误码（不包含通用码）
    USER_NOT_EXIST = 40401  # 用户不存在
    USERNAME_EXIST = 40001  # 用户名已存在
    EMAIL_EXIST = 40002  # 邮箱已注册


class UserException(HTTPException):
    def __init__(self,
                 code: CommonErrorCode | UserErrorCode,
                 message: str,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=code.value // 100, detail=message)
        self.code = code.value
        self.message = message  
        self.details = details
