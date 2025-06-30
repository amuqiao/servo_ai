from enum import Enum
from fastapi import status

class CommonErrorCode(Enum):
    # 通用成功/失败码
    SUCCESS = 20000  # 成功
    UNKNOWN_ERROR = 50000  # 未知错误
    # 通用业务操作码
    PARAM_VALIDATION_FAILED = 40003  # 参数验证失败
    DATABASE_OPERATION_FAILED = 50001  # 数据库操作失败
    SERVICE_UNAVAILABLE = 50300  # 服务不可用