from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import List

from src.schemas.timeseries_schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthCheckResponse,
    TimeSeriesData
)
from src.services.timeseries_service import timeseries_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["时间序列预测"])


@router.post("/", response_model=PredictionResponse)
async def predict_timeseries(request: PredictionRequest):
    """
    时间序列预测接口
    
    - **data**: 历史时间序列数据列表
    - **forecast_horizon**: 预测步长（默认24）
    - **context_length**: 上下文长度（可选）
    
    返回预测结果列表，包含时间戳、预测值和置信区间
    """
    logger.info(f"收到时间序列预测请求，数据点数量: {len(request.data)}, 预测步长: {request.forecast_horizon}")
    
    try:
        # 执行预测
        predictions = timeseries_service.predict(request)
        
        # 获取模型信息
        model_info = timeseries_service.get_model_info()
        
        # 构造响应
        response = PredictionResponse(
            code=200,
            message="预测成功",
            data=predictions,
            model_info={
                "model_name": model_info.model_name,
                "model_version": model_info.model_version,
                "context_length": model_info.context_length,
                "prediction_length": model_info.prediction_length
            },
            processing_time=0.0  # 实际处理时间在服务中计算
        )
        
        logger.info(f"预测完成，返回 {len(predictions)} 个预测结果")
        return response
        
    except ValueError as e:
        logger.error(f"预测参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预测服务异常: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    模型健康检查接口
    
    检查时间序列预测模型是否正常工作
    """
    logger.info("收到模型健康检查请求")
    
    try:
        # 执行健康检查
        is_healthy = timeseries_service.health_check()
        
        if is_healthy:
            model_info = timeseries_service.get_model_info()
            response = HealthCheckResponse(
                code=200,
                message="模型服务正常",
                data=model_info
            )
            logger.info("模型健康检查通过")
            return response
        else:
            logger.error("模型健康检查失败")
            raise HTTPException(status_code=503, detail="模型服务异常")
            
    except Exception as e:
        logger.error(f"健康检查异常: {str(e)}")
        raise HTTPException(status_code=503, detail=f"健康检查失败: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """
    获取模型信息接口
    
    返回当前使用的模型详细信息
    """
    logger.info("收到模型信息查询请求")
    
    try:
        model_info = timeseries_service.get_model_info()
        return {
            "code": 200,
            "message": "获取模型信息成功",
            "data": {
                "model_name": model_info.model_name,
                "model_version": model_info.model_version,
                "context_length": model_info.context_length,
                "prediction_length": model_info.prediction_length,
                "supported_frequencies": model_info.supported_frequencies
            }
        }
    except Exception as e:
        logger.error(f"获取模型信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@router.post("/test")
async def test_prediction():
    """
    测试预测接口
    
    使用示例数据进行预测测试
    """
    logger.info("收到测试预测请求")
    
    try:
        # 创建测试数据
        test_data = [
            TimeSeriesData(timestamp="2024-01-01T00:00:00", value=100.0),
            TimeSeriesData(timestamp="2024-01-01T01:00:00", value=101.0),
            TimeSeriesData(timestamp="2024-01-01T02:00:00", value=102.0),
            TimeSeriesData(timestamp="2024-01-01T03:00:00", value=103.0),
            TimeSeriesData(timestamp="2024-01-01T04:00:00", value=104.0),
            TimeSeriesData(timestamp="2024-01-01T05:00:00", value=105.0),
            TimeSeriesData(timestamp="2024-01-01T06:00:00", value=106.0),
            TimeSeriesData(timestamp="2024-01-01T07:00:00", value=107.0),
            TimeSeriesData(timestamp="2024-01-01T08:00:00", value=108.0),
            TimeSeriesData(timestamp="2024-01-01T09:00:00", value=109.0),
            TimeSeriesData(timestamp="2024-01-01T10:00:00", value=110.0),
            TimeSeriesData(timestamp="2024-01-01T11:00:00", value=111.0)
        ]
        
        test_request = PredictionRequest(
            data=test_data,
            forecast_horizon=6,
            context_length=8
        )
        
        # 执行预测
        predictions = timeseries_service.predict(test_request)
        
        # 构造响应
        response = PredictionResponse(
            code=200,
            message="测试预测成功",
            data=predictions,
            model_info={
                "model_name": "amazon/chronos-bolt-large",
                "model_version": "1.0.0",
                "test_mode": True
            },
            processing_time=0.0
        )
        
        logger.info(f"测试预测完成，返回 {len(predictions)} 个预测结果")
        return response
        
    except Exception as e:
        logger.error(f"测试预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试预测失败: {str(e)}") 