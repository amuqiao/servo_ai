from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from src.configs.database import get_db_conn
from src.services.ocr_service import OCRService
from src.services.task_service import TaskService
from src.models.ocr_model import OCRModel
from redis import Redis
from src.configs.redis_config import get_redis_client

from src.schemas.response_schema import BaseResponse
from src.schemas.ocr_task_schemas import OCRTaskResponse, OCRTaskData, CreateTasksRequest
from sqlalchemy.orm import Session
from src.configs import ApiConfig
import logging
from src.configs.database import get_db_conn
from src.services.ocr_service import OCRService
from src.services.redis_task_service import RedisTaskService

logger = logging.getLogger("celery")
router = APIRouter(prefix="/api/ocr", tags=["OCR任务处理"])

@router.post("/tasks/by-business-ids", response_model=OCRTaskResponse)
async def create_ocr_tasks_by_business_ids(
    business_ids: list[str] = Body(..., description="业务ID列表（电站编号）"),
    ai_status: int | None = None,
    db: Session = Depends(get_db_conn),
    redis_client: Redis = Depends(get_redis_client)
):
    """根据业务ID处理OCR任务接口（补全关联的公司ID）"""
    try:
        # 步骤1：通过业务ID查询关联的公司ID
        company_ids = await OCRService.fetch_company_ids_by_business_ids(business_ids, db)
        # 步骤2：查询待处理OCR记录
        records = await OCRService.fetch_ocr_records_by_business_ids(business_ids, db, ai_status=ai_status)
        
        if not records:
            return OCRTaskResponse(
                message="没有找到对应的OCR记录",
                data=OCRTaskData(
                    task_ids=[], 
                    count=0, 
                    business_ids=business_ids,  # 原始业务ID
                    company_ids=company_ids  # 关联的公司ID
                )
            )
        
        task_ids = []
        for record in records:
            # 使用TaskService创建任务
            original_urls = record.url.split(',') if record.url else []
            config = ApiConfig()
            urls = [f"{config.dify.OCR_BASE_URL}{url}" for url in original_urls]
            task = TaskService.create_task(
                task_type="ocr_cert_processing",
                content={"urls": urls},
                task_id=f"{record.id}_{record.business_id}"
            )
            # 发布任务到Redis队列
            TaskService.publish_task(task, redis_client)
            task_ids.append(task.task_id)
        
        return OCRTaskResponse(
            message="任务创建成功",
            data=OCRTaskData(
                task_ids=task_ids,
                count=len(task_ids),
                business_ids=business_ids,  # 原始业务ID
                company_ids=company_ids  # 关联的公司ID
            )
        )
    except Exception as e:
        logger.error(f"业务ID任务处理异常：{business_ids}，错误：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.post("/tasks/by-company-ids", response_model=OCRTaskResponse)
async def create_ocr_tasks_by_company_ids(
    company_ids: list[str] = Body(..., description="公司ID列表"),
    ai_status: int | None = None,
    db: Session = Depends(get_db_conn),
    redis_client: Redis = Depends(get_redis_client)
):
    """根据公司ID处理OCR任务接口（补全关联的业务ID）"""
    try:
        # 步骤1：通过公司ID查询关联的业务ID（电站编号）
        business_ids = await OCRService.fetch_business_ids_by_company_ids(company_ids, db)
        # 步骤2：查询待处理OCR记录
        records = await OCRService.fetch_ocr_records_by_company_ids(company_ids, db, ai_status=ai_status)
        
        if not records:
            return OCRTaskResponse(
                message="未找到待处理的OCR记录",
                data=OCRTaskData(
                    company_ids=company_ids,  # 原始公司ID
                    task_ids=[], 
                    count=0,
                    business_ids=business_ids  # 关联的业务ID
                )
            )
        
        task_ids = []
        for record in records:
            # 使用TaskService创建任务
            original_urls = record.url.split(',') if record.url else []
            config = ApiConfig()
            urls = [f"{config.dify.OCR_BASE_URL}{url}" for url in original_urls]
            task = TaskService.create_task(
                task_type="ocr_cert_processing",
                content={"urls": urls},
                task_id=f"{record.id}_{record.business_id}"
            )
            # 发布任务到Redis队列
            TaskService.publish_task(task, redis_client)
            task_ids.append(task.task_id)
        
        return OCRTaskResponse(
            message="任务创建成功",
            data=OCRTaskData(
                company_ids=company_ids,  # 原始公司ID
                task_ids=task_ids,
                count=len(task_ids),
                business_ids=business_ids  # 关联的业务ID
            )
        )
    except Exception as e:
        logger.error(f"公司ID任务处理异常：{company_ids}，错误：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.post("/tasks", response_model=OCRTaskResponse)
async def create_ocr_tasks(
    limit: int,
    ai_status: int | None = None,
    db: Session = Depends(get_db_conn),
    redis_client: Redis = Depends(get_redis_client)
):
    """处理OCR任务接口（优化版本，补充业务ID和公司ID）"""
    if limit <= 0:
        logger.warning("接口参数校验失败：limit必须大于0")
        raise HTTPException(status_code=400, detail="请求数量必须大于0")

    try:
        records = await OCRService.fetch_ocr_records(limit, db, ai_status=ai_status)
        if not records:
            return OCRTaskResponse(
                message="没有可处理的记录",
                data=OCRTaskData(task_ids=[], count=0, business_ids=[], company_ids=[])
            )
        
        # 提取业务ID列表
        business_ids = list({record.business_id for record in records if record.business_id})
        # 通过业务ID查询关联的公司ID
        company_ids = await OCRService.fetch_company_ids_by_business_ids(business_ids, db) if business_ids else []
        
        task_ids = []
        for record in records:
            # 使用TaskService创建任务
            original_urls = record.url.split(',') if record.url else []
            config = ApiConfig()
            urls = [f"{config.dify.OCR_BASE_URL}{url}" for url in original_urls]
            task = TaskService.create_task(
                task_type="ocr_cert_processing",
                content={"urls": urls},
                task_id=f"{record.id}_{record.business_id}"  # 确保使用此格式
            )
            # 发布任务到Redis队列
            TaskService.publish_task(task, redis_client)
            task_ids.append(task.task_id)
        
        return OCRTaskResponse(
            message="任务创建成功",
            data=OCRTaskData(
                task_ids=task_ids,
                count=len(task_ids),
                business_ids=business_ids,
                company_ids=company_ids
            )
        )
    except Exception as e:
        logger.error(f"OCR任务处理异常：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")
