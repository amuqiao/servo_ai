from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from typing import Dict, Any, Optional, Type
from src.schemas.response_schema import ErrorResponse

# 导入所有自定义异常类（可扩展）
from src.exceptions.user_exceptions import UserException
from src.exceptions.redis_exceptions import RedisException
from src.exceptions.work_order_exceptions import WorkOrderException 
from src.exceptions.taxpayer_cert_exceptions import TaxpayerCertException

logger = logging.getLogger(__name__)


def generic_exception_handler(exc_type: Type[Exception]):
    """通用异常处理函数生成器，支持动态获取异常属性"""
    async def handler(request: Request, exc: exc_type):
        logger.error(f"{exc_type.__name__}业务异常: {exc.message}", exc_info=True)
        return JSONResponse(
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                status_code=exc.status_code
            ).dict(),
            status_code=exc.status_code
        )
    return handler


# 异常处理映射表（核心扩展点）
# 异常处理映射表
EXCEPTION_HANDLERS_MAP: Dict[Type[Exception], Any] = {
    UserException: generic_exception_handler(UserException),
    RedisException: generic_exception_handler(RedisException),
    WorkOrderException: generic_exception_handler(WorkOrderException),  
    TaxpayerCertException: generic_exception_handler(TaxpayerCertException),  
}


def add_exception_handlers(app: FastAPI) -> None:
    """通用异常处理器注册函数（自动遍历映射表注册）"""
    # 注册自定义业务异常处理器
    for exc_type, handler in EXCEPTION_HANDLERS_MAP.items():
        app.add_exception_handler(exc_type, handler)

    # 注册框架级异常处理器（保持原有逻辑）
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"请求验证错误: {exc}", exc_info=True)
        errors = [{
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        } for error in exc.errors()]
        return JSONResponse(
            content=ErrorResponse(
                code=40000,
                message="请求参数验证失败",
                details={"errors": errors},
                status_code=status.HTTP_400_BAD_REQUEST
            ).dict(),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        logger.error(f"Pydantic验证错误: {exc}", exc_info=True)
        return JSONResponse(
            content=ErrorResponse(
                code=40000,
                message="数据验证失败",
                details={"errors": exc.errors()},
                status_code=status.HTTP_400_BAD_REQUEST
            ).dict(),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"未捕获的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            content=ErrorResponse(
                code=50000,
                message="服务器内部错误，请稍后重试",
                details=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).dict(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
