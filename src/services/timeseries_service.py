import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests
import json
from src.schemas.timeseries_schemas import (
    TimeSeriesData, 
    PredictionResult, 
    ModelInfo,
    PredictionRequest
)

logger = logging.getLogger(__name__)


class TimeSeriesPredictionService:
    """时间序列预测服务"""
    
    def __init__(self):
        self.model_name = "amazon/chronos-bolt-large"
        self.model_version = "1.0.0"
        self.context_length = 512
        self.prediction_length = 24
        self.supported_frequencies = ["H", "D", "W", "M", "Q", "Y"]
        
        # AWS SageMaker 端点配置 (需要根据实际情况配置)
        self.endpoint_name = "chronos-bolt-large-endpoint"
        self.region = "us-east-1"
        self.sagemaker_url = f"https://runtime.sagemaker.{self.region}.amazonaws.com/endpoints/{self.endpoint_name}/invocations"
        
        # 备用本地模型配置
        self.use_local_model = True  # 如果AWS端点不可用，使用本地模型
        self.local_model_path = "./models/chronos-bolt-large"
        
    def _prepare_data(self, data: List[TimeSeriesData]) -> np.ndarray:
        """准备数据格式"""
        try:
            # 转换为DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': item.timestamp if isinstance(item.timestamp, str) else item.timestamp.isoformat(),
                    'value': item.value
                }
                for item in data
            ])
            
            # 确保时间戳格式正确
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # 提取数值序列
            values = df['value'].values.astype(np.float32)
            
            logger.info(f"数据准备完成，序列长度: {len(values)}")
            return values
            
        except Exception as e:
            logger.error(f"数据准备失败: {str(e)}")
            raise ValueError(f"数据格式错误: {str(e)}")
    
    def _call_aws_sagemaker(self, data: np.ndarray, forecast_horizon: int) -> np.ndarray:
        """调用AWS SageMaker端点"""
        try:
            payload = {
                "instances": [
                    {
                        "data": data.tolist(),
                        "forecast_horizon": forecast_horizon
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(
                self.sagemaker_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                predictions = np.array(result['predictions'][0])
                logger.info(f"AWS SageMaker预测成功，预测长度: {len(predictions)}")
                return predictions
            else:
                logger.error(f"AWS SageMaker调用失败: {response.status_code} - {response.text}")
                raise Exception(f"AWS SageMaker调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"AWS SageMaker调用异常: {str(e)}")
            raise
    
    def _call_local_model(self, data: np.ndarray, forecast_horizon: int) -> np.ndarray:
        """调用本地模型（模拟实现）"""
        try:
            # 这里是一个简化的本地模型实现
            # 实际项目中应该加载真实的Chronos模型
            
            # 使用简单的移动平均作为示例
            window_size = min(7, len(data))
            if window_size > 0:
                last_values = data[-window_size:]
                trend = np.mean(np.diff(last_values)) if len(last_values) > 1 else 0
                
                # 生成预测
                predictions = []
                last_value = data[-1]
                
                for i in range(forecast_horizon):
                    # 添加趋势和随机噪声
                    predicted = last_value + trend * (i + 1) + np.random.normal(0, 0.1)
                    predictions.append(predicted)
                    last_value = predicted
                
                predictions = np.array(predictions)
                logger.info(f"本地模型预测成功，预测长度: {len(predictions)}")
                return predictions
            else:
                raise ValueError("数据长度不足，无法进行预测")
                
        except Exception as e:
            logger.error(f"本地模型调用异常: {str(e)}")
            raise
    
    def predict(self, request: PredictionRequest) -> List[PredictionResult]:
        """执行时间序列预测"""
        start_time = time.time()
        
        try:
            # 数据验证
            if len(request.data) < 2:
                raise ValueError("历史数据至少需要2个数据点")
            
            # 准备数据
            historical_data = self._prepare_data(request.data)
            
            # 确定上下文长度
            context_length = request.context_length or min(self.context_length, len(historical_data))
            if context_length > len(historical_data):
                context_length = len(historical_data)
            
            # 使用最近的context_length个数据点
            input_data = historical_data[-context_length:]
            
            # 执行预测
            if self.use_local_model:
                predictions = self._call_local_model(input_data, request.forecast_horizon)
            else:
                predictions = self._call_aws_sagemaker(input_data, request.forecast_horizon)
            
            # 生成预测结果
            results = []
            last_timestamp = request.data[-1].timestamp
            if isinstance(last_timestamp, str):
                last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            
            for i, pred_value in enumerate(predictions):
                # 假设数据是小时级别的，可以根据实际情况调整
                pred_timestamp = last_timestamp + timedelta(hours=i+1)
                
                # 计算置信区间（简化实现）
                confidence_range = pred_value * 0.1  # 10%的置信区间
                
                result = PredictionResult(
                    timestamp=pred_timestamp,
                    predicted_value=float(pred_value),
                    confidence_lower=float(pred_value - confidence_range),
                    confidence_upper=float(pred_value + confidence_range)
                )
                results.append(result)
            
            processing_time = time.time() - start_time
            logger.info(f"预测完成，处理时间: {processing_time:.2f}秒")
            
            return results
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            raise
    
    def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        return ModelInfo(
            model_name=self.model_name,
            model_version=self.model_version,
            context_length=self.context_length,
            prediction_length=self.prediction_length,
            supported_frequencies=self.supported_frequencies
        )
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的健康检查：使用测试数据
            test_data = [
                TimeSeriesData(timestamp="2024-01-01T00:00:00", value=100.0),
                TimeSeriesData(timestamp="2024-01-01T01:00:00", value=101.0),
                TimeSeriesData(timestamp="2024-01-01T02:00:00", value=102.0)
            ]
            
            test_request = PredictionRequest(
                data=test_data,
                forecast_horizon=1
            )
            
            self.predict(test_request)
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False


# 创建全局服务实例
timeseries_service = TimeSeriesPredictionService() 