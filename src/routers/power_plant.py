from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models.power_plant_model import PompPowerPlantBasic
from src.configs.database import get_db_conn
from src.schemas.power_plant_schemas import (
    PowerPlantInfo,
    PowerPlantListData,
    PowerPlantDetailResponse,
    PowerPlantListResponse
)  # 导入新响应模型
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/power-plants", tags=["电站管理"])


def get_base_power_plant_query():
    """公共查询逻辑（提取所有核心字段）
    作用：避免重复编写字段选择代码，统一查询字段
    返回：包含id、power_number、company_id、company_name、province的SQLAlchemy查询对象
    """
    return select(
        PompPowerPlantBasic.id,
        PompPowerPlantBasic.power_number,
        PompPowerPlantBasic.company_id,
        PompPowerPlantBasic.company_name,
        PompPowerPlantBasic.province
    )


@router.get("/power-numbers", response_model=PowerPlantListResponse)  
async def get_power_numbers(company_id: int, db: Session = Depends(get_db_conn)):
    """根据公司ID获取电站编号接口
    - 参数：company_id（整数，必填，目标公司ID）
    - 返回：统一响应对象（包含电站基础信息列表及数量）
    """
    logger.info(f"开始处理获取电站编号请求，公司ID：{company_id}")
    try:
        query = get_base_power_plant_query().where(
            PompPowerPlantBasic.company_id == company_id
        )
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        # 构造列表数据结构（解耦数据与数量）
        list_data = PowerPlantListData(data=plants, count=len(plants))
        logger.info(f"成功获取公司ID {company_id} 的电站编号，数量：{len(plants)}")
        return PowerPlantListResponse(data=list_data)  # 使用明确的响应模型
    except Exception as e:
        logger.error(f"获取电站编号失败，公司ID {company_id}，错误详情：{str(e)}")
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")


@router.get("/province-companies", response_model=PowerPlantListResponse)  
async def get_companies_by_provinces(
    provinces: list[str] = Query(..., description="多省份ID列表，示例：?provinces=140000&provinces=530000"),
    db: Session = Depends(get_db_conn)
):
    """根据多省份ID获取公司信息接口
    - 参数：provinces（字符串列表，必填，省份编码列表）
    - 返回：统一响应对象（包含公司关联的电站基础信息列表及数量）
    """
    logger.info(f"开始处理多省份公司信息请求，省份列表：{provinces}")
    if not provinces:
        logger.warning("省份ID列表为空，返回400错误")
        raise HTTPException(status_code=400, detail="省份ID列表不能为空")

    try:
        query = get_base_power_plant_query().where(
            PompPowerPlantBasic.province.in_(provinces),
            PompPowerPlantBasic.company_id.isnot(None),
            PompPowerPlantBasic.company_name.isnot(None)
        ).group_by(
            PompPowerPlantBasic.company_id,
            PompPowerPlantBasic.company_name
        )
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        # 构造列表数据结构
        list_data = PowerPlantListData(data=plants, count=len(plants))
        logger.info(f"成功获取省份 {provinces} 的公司信息，数量：{len(plants)}")
        return PowerPlantListResponse(data=list_data)  # 使用明确的响应模型
    except Exception as e:
        logger.error(f"多省份公司信息查询失败，省份列表 {provinces}，错误详情：{str(e)}")
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")


@router.get("/", response_model=PowerPlantListResponse)  
async def get_plants(limit: int = 10, db: Session = Depends(get_db_conn)):
    """获取电站列表接口（分页简化版）
    - 参数：limit（整数，选填，默认10，最大返回数量）
    - 返回：统一响应对象（包含电站基础信息列表及数量）
    """
    logger.info(f"开始处理电站列表请求，最大返回数量：{limit}")
    if limit <= 0:
        logger.warning(f"无效的查询数量：{limit}，返回400错误")
        raise HTTPException(status_code=400, detail="查询数量必须大于0")

    try:
        query = get_base_power_plant_query().where(
            PompPowerPlantBasic.company_id.isnot(None),
            PompPowerPlantBasic.company_name.isnot(None),
            PompPowerPlantBasic.province.isnot(None)
        ).limit(limit)
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        # 构造列表数据结构
        list_data = PowerPlantListData(data=plants, count=len(plants))
        logger.info(f"成功获取电站列表，实际返回数量：{len(plants)}")
        return PowerPlantListResponse(
            code=200,
            message="查询成功",
            data=list_data
        )  # 使用明确的响应模型
    except Exception as e:
        logger.error(f"电站列表查询失败，最大数量 {limit}，错误详情：{str(e)}")
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")
