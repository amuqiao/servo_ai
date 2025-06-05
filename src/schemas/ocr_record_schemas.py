from pydantic import BaseModel
from typing import Optional, List
from src.schemas.response_schema import BaseResponse  # 导入统一响应体

# 基础业务数据模型（纯数据描述）
class OCRRecordInfo(BaseModel):
    """OCR记录基础信息模型（解耦合业务数据与响应结构）"""
    id: int
    status: int
    business_id: str
    object_id: str
    name: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    ai_task_id: Optional[str] = None
    ai_status: Optional[int] = None
    ai_content: Optional[str] = None
    batch_no: Optional[str] = None

    class Config:
        from_attributes = True  # 支持从ORM对象映射

# 列表数据封装模型（解耦数据与数量）
class OCRListData(BaseModel):
    """OCR记录列表数据封装模型"""
    records: List[OCRRecordInfo] | None = None  # 重命名为records，明确表示数据列表
    count: int  # 列表长度统计

# 详情响应模型（继承BaseResponse，明确data类型）
class OCRDetailResponse(BaseResponse):
    """单个OCR记录详情响应模型"""
    data: OCRRecordInfo | None = None  # 明确data为单个业务模型或None

# 列表响应模型（继承BaseResponse）
class OCRListResponse(BaseResponse):
    """OCR记录列表响应模型"""
    data: OCRListData | None = None  # 包含列表数据和数量统计

# 更新AI状态专用数据模型（明确响应数据结构）
class OCRUpdateAIStatusData(BaseModel):
    """批量更新AI状态的响应数据模型"""
    updated_count: int  # 明确更新数量类型

# 更新AI状态响应模型（继承BaseResponse，使用专用数据模型）
class OCRUpdateAIStatusResponse(BaseResponse):
    """批量更新AI状态的响应模型"""
    data: OCRUpdateAIStatusData | None = None  # 明确data为更新结果数据模型

# 批量更新请求模型（保持简洁）
class OCRUpdateAIStatusRequest(BaseModel):
    """批量更新AI状态的请求模型"""
    business_ids: List[str]  # 业务ID列表

# 新增：统计请求模型（支持公司/省份筛选）
# 统计请求模型（仅保留ID筛选）
class OCRStatusStatisticsRequest(BaseModel):
    company_ids: List[int] | None = None  # 公司ID列表（可选）
    province_ids: List[str] | None = None  # 省份代码列表（可选）

# 新增：统计结果数据模型
class OCRStatusStatisticsData(BaseModel):
    ai_status_neg_1_count: int  # 处理失败数量（原ai_status_-1_count）
    ai_status_0_count: int   # 未处理数量
    ai_status_1_count: int   # 处理成功数量
    total_power_plants: int  # 符合条件的电站总数（去重business_id）

# 新增：统计响应模型
class OCRStatusStatisticsResponse(BaseResponse):
    data: OCRStatusStatisticsData | None = None

# 新增：根据公司ID更新ai_status的请求模型
class OCRUpdateAIStatusByCompanyRequest(BaseModel):
    company_ids: List[str]  # 公司ID列表