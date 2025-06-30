from pydantic import BaseModel
from typing import List, Optional
from src.schemas.response_schema import BaseResponse  # 导入统一响应体

# 基础数据模型（纯业务数据描述）
class PowerPlantInfo(BaseModel):
    """电站基础信息模型"""
    id: str
    power_number: str
    company_id: int
    company_name: str
    province: str

    class Config:
        from_attributes = True  # 支持从ORM对象映射


# 列表数据封装模型（解耦数据与数量）
class PowerPlantListData(BaseModel):
    """电站列表数据封装模型"""
    data: List[PowerPlantInfo] | None = None  # 电站信息列表
    count: int  # 列表长度统计


# 响应模型（直接继承BaseResponse，明确data类型）
class PowerPlantDetailResponse(BaseResponse):
    """单个电站详情响应模型"""
    data: PowerPlantInfo | None = None  # 明确data为单个电站信息或None


class PowerPlantListResponse(BaseResponse):
    """电站列表响应模型"""
    data: PowerPlantListData | None = None  # 包含列表数据和数量统计