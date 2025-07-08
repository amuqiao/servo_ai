from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from datetime import datetime
import numpy as np


class TimeSeriesData(BaseModel):
    """时间序列数据模型"""
    timestamp: Union[str, datetime] = Field(..., description="时间戳")
    value: float = Field(..., description="数值")


class PredictionRequest(BaseModel):
    """预测请求模型"""
    data: List[TimeSeriesData] = Field(..., description="历史时间序列数据")
    forecast_horizon: int = Field(default=24, ge=1, le=1000, description="预测步长")
    context_length: Optional[int] = Field(default=None, ge=1, le=10000, description="上下文长度")
    
    class Config:
        json_encoders = {
            np.ndarray: lambda v: v.tolist(),
            np.float32: lambda v: float(v),
            np.float64: lambda v: float(v),
            np.int32: lambda v: int(v),
            np.int64: lambda v: int(v),
        }


class PredictionResult(BaseModel):
    """预测结果模型"""
    timestamp: Union[str, datetime] = Field(..., description="预测时间戳")
    predicted_value: float = Field(..., description="预测值")
    confidence_lower: Optional[float] = Field(None, description="置信区间下界")
    confidence_upper: Optional[float] = Field(None, description="置信区间上界")


class PredictionResponse(BaseModel):
    """预测响应模型"""
    code: int = 200
    message: str = "预测成功"
    data: List[PredictionResult] = Field(..., description="预测结果列表")
    model_info: dict = Field(default_factory=dict, description="模型信息")
    processing_time: float = Field(..., description="处理时间(秒)")


class ModelInfo(BaseModel):
    """模型信息模型"""
    model_name: str = Field(..., description="模型名称")
    model_version: str = Field(..., description="模型版本")
    context_length: int = Field(..., description="上下文长度")
    prediction_length: int = Field(..., description="预测长度")
    supported_frequencies: List[str] = Field(default_factory=list, description="支持的频率")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    code: int = 200
    message: str = "模型服务正常"
    data: ModelInfo = Field(..., description="模型信息") 