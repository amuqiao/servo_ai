from fastapi import HTTPException
from enum import Enum
from .common_exceptions import CommonErrorCode
from typing import Dict, Any, Optional


class TaxpayerCertErrorCode(Enum):
    # 纳税人证明识别业务错误码（遵循500xx系列）
    OCR_API_KEY_MISSING = 50020  # OCR API密钥未配置
    OCR_TIMEOUT = 50021  # OCR识别超时
    OCR_PARSE_FAILED = 50022  # OCR结果解析失败
    OCR_SERVICE_ERROR = 50023  # OCR服务调用失败


class TaxpayerCertException(HTTPException):
    def __init__(
        self,
        code: CommonErrorCode | TaxpayerCertErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        status_code = code.value // 100
        super().__init__(status_code=status_code, detail=message)
        self.code = code.value
        self.message = message
        self.details = details