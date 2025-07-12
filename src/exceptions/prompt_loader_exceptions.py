from fastapi import HTTPException
from enum import Enum
from .common_exceptions import CommonErrorCode
from typing import Dict, Any, Optional


class PromptLoaderErrorCode(Enum):
    # 提示词加载错误码（遵循500xx系列）
    PROMPT_FILE_NOT_FOUND = 50030  # 提示词文件不存在
    PROMPT_FILE_INVALID = 50031  # 提示词文件格式无效
    PROMPT_EMPTY = 50032  # 提示词内容为空
    PROMPT_LOAD_FAILED = 50033  # 提示词加载失败


class PromptLoaderException(HTTPException):
    def __init__(
        self,
        code: CommonErrorCode | PromptLoaderErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        status_code = code.value // 100
        super().__init__(status_code=status_code, detail=message)
        self.code = code.value
        self.message = message
        self.details = details