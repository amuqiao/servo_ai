from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  # 导入SQLAlchemy会话类（用于数据库依赖注入）
from src.configs import ApiConfig
import uuid
import logging
import json
from src.configs.redis_config import get_redis_client  # Redis连接生成器
from src.configs.database import get_db_conn  # 数据库连接依赖
from src.services.ocr_service import OCRService  # OCR业务逻辑服务
from src.models import OCRModel  # OCR记录ORM模型
from src.services.redis_task_service import RedisTaskService

logger = logging.getLogger("celery")

# 定义OCR任务处理路由（前缀/api/ocr，标签OCR任务处理）
router = APIRouter(prefix="/api/ocr", tags=["OCR任务处理"])

@router.post("/tasks")
async def create_ocr_tasks(limit: int, db: Session = Depends(get_db_conn)):
    """
    处理OCR任务接口（基础版本）
    :param limit: 需要获取的待处理OCR记录数量（必须大于0）
    :param db: 数据库会话（通过FastAPI依赖注入自动管理生命周期）
    :return: 生成的Redis任务ID列表
    """
    if limit <= 0:
        logger.warning("接口参数校验失败：limit必须大于0")
        raise HTTPException(status_code=400, detail="请求数量必须大于0")

    try:
        logger.info(f"开始获取待处理OCR记录，限制数量：{limit}")
        # 调用OCR服务获取待处理记录（AI状态未完成或为空）
        records = await OCRService.fetch_ocr_records(limit, db)
        if not records:
            logger.info("未找到可处理的OCR记录")
            return {"task_ids": [], "message": "没有可处理的记录"}
        
        task_ids = await RedisTaskService.process_records_to_tasks(records)  # 调用服务层方法
        logger.info(f"成功生成{len(task_ids)}个OCR任务")
        return {"task_ids": task_ids}
    except HTTPException as he:
        raise  # 直接抛出FastAPI异常（已包含状态码和详情）
    except Exception as e:
        logger.error(f"OCR任务处理异常，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.post("/tasks/by-business-ids")
async def create_ocr_tasks_by_business_ids(business_ids: list[str], db: Session = Depends(get_db_conn)):
    """
    根据业务ID处理OCR任务接口
    :param business_ids: 业务ID列表（如电厂编号）
    :param db: 数据库会话（依赖注入）
    :return: 生成的Redis任务ID列表
    """
    try:
        logger.info(f"开始根据业务ID获取OCR记录，业务ID数量：{len(business_ids)}")
        # 调用OCR服务获取匹配的待处理记录
        records = await OCRService.fetch_ocr_records_by_business_ids(business_ids, db)
        if not records:
            logger.info("未找到匹配业务ID的OCR记录")
            return {"task_ids": [], "message": "没有找到对应的OCR记录"}
        
        task_ids = await RedisTaskService.process_records_to_tasks(records)  # 调用服务层方法
        logger.info(f"成功生成{len(task_ids)}个业务ID关联OCR任务")
        return {"task_ids": task_ids}
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"业务ID任务处理异常，业务ID列表：{business_ids}，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.post("/tasks/by-company-ids")
async def create_ocr_tasks_by_company_ids(company_ids: list[str], db: Session = Depends(get_db_conn)):
    """
    根据公司ID列表处理OCR任务接口（优化后）
    :param company_ids: 公司ID列表
    :param db: 数据库会话（依赖注入）
    :return: 公司ID关联的任务创建结果（包含任务ID列表）
    """
    try:
        logger.info(f"开始根据公司ID获取关联的待处理OCR记录，公司ID数量：{len(company_ids)}")
        # 直接调用整合后的服务方法获取记录
        records = await OCRService.fetch_ocr_records_by_company_ids(company_ids, db)
        if not records:
            logger.info("未找到公司ID关联的待处理OCR记录")
            return {"company_ids": company_ids, "task_count": 0, "task_ids": [], "message": "未找到待处理的OCR记录"}
        
        task_ids = await RedisTaskService.process_records_to_tasks(records)  # 调用服务层方法生成任务ID
        logger.info(f"成功生成{len(task_ids)}个公司ID关联OCR任务")
        return {
            "company_ids": company_ids,
            "task_count": len(task_ids),
            "task_ids": task_ids,
            "message": "任务创建成功"
        }
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"公司ID任务处理异常，公司ID列表：{company_ids}，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")
