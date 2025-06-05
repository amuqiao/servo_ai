from pydantic import BaseModel
from typing import Any


class BaseResponse(BaseModel):
    code: int = 200  # 默认成功状态码
    message: str = "操作成功"  # 默认成功消息
    data: Any = None
