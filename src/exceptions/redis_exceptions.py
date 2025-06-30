from fastapi import HTTPException
from enum import Enum
from .common_exceptions import CommonErrorCode  # 导入通用码
from typing import Dict, Any, Optional

class RedisErrorCode(Enum):
    # 业务专属错误码（不包含通用码）
    KEY_NOT_EXIST = 40401  # 键不存在（对应HTTP 404状态码）
    KEY_CREATE_FAILED = 50002  # 键创建失败
    KEY_UPDATE_FAILED = 50003  # 键更新失败
    KEY_DELETE_FAILED = 50004  # 键删除失败
    OPERATION_FAILED = 50001  # 通用操作失败

class RedisException(HTTPException):
    def __init__(
        self,
        code: CommonErrorCode | RedisErrorCode,  # 支持通用码或业务码
        message: str,
        details: Optional[Dict[str, Any]] = None):
        status_code = code.value // 100  # 从错误码中提取HTTP状态码
        super().__init__(status_code=status_code, detail=message)
        self.code = code.value  # 业务错误码
        self.message = message
        self.details = details
