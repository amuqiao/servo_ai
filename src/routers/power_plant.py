from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models.power_plant_model import PowerPlantModel
from src.configs.database import get_db_conn
from pydantic import BaseModel
import logging  # 新增：导入日志模块

# 初始化日志记录器（使用当前模块名）
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/power-plants", tags=["电站管理"])


class PowerPlantInfo(BaseModel):
    """电站基础信息模型（Pydantic模型）
    字段说明：
    - id: 电站唯一标识（字符串类型）
    - power_number: 电站编号（字符串类型）
    - company_id: 所属公司ID（整数类型）
    - company_name: 所属公司名称（字符串类型）
    - province: 所属省份编码（字符串类型，如"140000"）
    """
    id: str
    power_number: str
    company_id: int
    company_name: str
    province: str

    class Config:
        from_attributes = True


class CommonResponse(BaseModel):
    """统一响应模型（所有接口返回此结构）
    字段说明：
    - code: 状态码（默认200表示成功）
    - message: 提示信息（默认"请求成功"）
    - data: 具体数据列表（默认空列表）
    """
    code: int = 200
    message: str = "请求成功"
    data: list[PowerPlantInfo] = []

    class Config:
        from_attributes = True


def get_base_power_plant_query():
    """公共查询逻辑（提取所有核心字段）
    作用：避免重复编写字段选择代码，统一查询字段
    返回：包含id、power_number、company_id、company_name、province的SQLAlchemy查询对象
    """
    return select(
        PowerPlantModel.id,
        PowerPlantModel.power_number,
        PowerPlantModel.company_id,
        PowerPlantModel.company_name,
        PowerPlantModel.province
    )


@router.get("/power-numbers", response_model=CommonResponse)
async def get_power_numbers(company_id: int, db: Session = Depends(get_db_conn)):
    """根据公司ID获取电站编号接口
    - 参数：company_id（整数，必填，目标公司ID）
    - 返回：统一响应对象（包含电站基础信息列表）
    """
    logger.info(f"开始处理获取电站编号请求，公司ID：{company_id}")  # 新增：记录处理开始
    try:
        query = get_base_power_plant_query().where(
            PowerPlantModel.company_id == company_id
        )
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        logger.info(f"成功获取公司ID {company_id} 的电站编号，数量：{len(plants)}")  # 新增：记录处理结果
        return {"data": plants}
    except Exception as e:
        logger.error(f"获取电站编号失败，公司ID {company_id}，错误详情：{str(e)}")  # 新增：记录异常信息
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")


@router.get("/province-companies", response_model=CommonResponse)
async def get_companies_by_provinces(
    provinces: list[str] = Query(..., description="多省份ID列表，示例：?provinces=140000&provinces=530000"),
    db: Session = Depends(get_db_conn)
):
    """根据多省份ID获取公司信息接口
    - 参数：provinces（字符串列表，必填，省份编码列表）
    - 返回：统一响应对象（包含公司关联的电站基础信息列表）
    """
    logger.info(f"开始处理多省份公司信息请求，省份列表：{provinces}")  # 新增：记录处理开始
    if not provinces:
        logger.warning("省份ID列表为空，返回400错误")  # 新增：记录警告信息
        raise HTTPException(status_code=400, detail="省份ID列表不能为空")

    try:
        query = get_base_power_plant_query().where(
            PowerPlantModel.province.in_(provinces),
            PowerPlantModel.company_id.isnot(None),
            PowerPlantModel.company_name.isnot(None)
        ).group_by(
            PowerPlantModel.company_id,
            PowerPlantModel.company_name
        )
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        logger.info(f"成功获取省份 {provinces} 的公司信息，数量：{len(plants)}")  # 新增：记录处理结果
        return {"data": plants}
    except Exception as e:
        logger.error(f"多省份公司信息查询失败，省份列表 {provinces}，错误详情：{str(e)}")  # 新增：记录异常信息
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")


@router.get("/", response_model=CommonResponse)
async def get_plants(limit: int = 10, db: Session = Depends(get_db_conn)):
    """获取电站列表接口（分页简化版）
    - 参数：limit（整数，选填，默认10，最大返回数量）
    - 返回：统一响应对象（包含电站基础信息列表）
    """
    logger.info(f"开始处理电站列表请求，最大返回数量：{limit}")  # 新增：记录处理开始
    if limit <= 0:
        logger.warning(f"无效的查询数量：{limit}，返回400错误")  # 新增：记录警告信息
        raise HTTPException(status_code=400, detail="查询数量必须大于0")

    try:
        query = get_base_power_plant_query().where(
            PowerPlantModel.company_id.isnot(None),
            PowerPlantModel.company_name.isnot(None),
            PowerPlantModel.province.isnot(None)
        ).limit(limit)
        result = db.execute(query)
        plants = [PowerPlantInfo(**row._asdict()) for row in result]
        logger.info(f"成功获取电站列表，实际返回数量：{len(plants)}")  # 新增：记录处理结果
        return {"data": plants}
    except Exception as e:
        logger.error(f"电站列表查询失败，最大数量 {limit}，错误详情：{str(e)}")  # 新增：记录异常信息
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")
