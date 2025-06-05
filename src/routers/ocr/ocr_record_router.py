from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List
from src.schemas.response_schema import BaseResponse
# 导入优化后的专用schemas
from src.schemas.ocr_record_schemas import (
    OCRRecordInfo,
    OCRDetailResponse,
    OCRListResponse,
    OCRListData,
    OCRUpdateAIStatusRequest,
    OCRUpdateAIStatusResponse,
    OCRUpdateAIStatusData,
    OCRStatusStatisticsResponse,
    OCRStatusStatisticsRequest,
    OCRStatusStatisticsData,
    OCRUpdateAIStatusByCompanyRequest  # 新增：导入新增的请求模型类
)
import logging
# 新增：导入OCRService类
from src.services.ocr_service import OCRService

from src.models.ocr_model import OCRModel
from src.configs.database import get_db_conn

router = APIRouter(
    prefix="/api/ocr-records",
    tags=["OCR识别结果"],
    responses={
        400: {"description": "参数错误", "model": BaseResponse},
        500: {"description": "服务器错误", "model": BaseResponse}
    }
)
logger = logging.getLogger(__name__)

@router.get("", response_model=OCRListResponse)
async def get_ocr_records_by_business_ids(
    business_ids: list[str] = Query(..., description="业务ID列表"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_conn)
):
    if not business_ids:
        logger.warning("业务ID列表不能为空")
        raise HTTPException(status_code=400, detail="业务ID列表不能为空")

    logger.info(f"批量查询业务ID: {business_ids} 页码: {page} 每页数量: {page_size}")
    try:
        query = db.query(OCRModel).filter(
            OCRModel.business_id.in_(business_ids),
            OCRModel.is_delete == 0
        )
        records = query.offset((page - 1) * page_size).limit(page_size).all()
        total = query.count()

        if not records:
            logger.warning(f"未找到业务ID为 {business_ids} 的记录")
            raise HTTPException(status_code=404, detail="未找到相关记录")

        # 转换ORM对象为业务模型列表
        record_infos = [OCRRecordInfo.model_validate(record) for record in records]
        return OCRListResponse(
            message="查询成功",
            data=OCRListData(records=record_infos, count=total)  # 使用records字段
        )
    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/update-ai-status", response_model=OCRUpdateAIStatusResponse)
async def update_ai_status_by_business_ids(
    request: OCRUpdateAIStatusRequest = Body(...),
    db: Session = Depends(get_db_conn)
):
    if not request.business_ids:
        logger.warning("业务ID列表不能为空")
        raise HTTPException(status_code=400, detail="业务ID列表不能为空")

    try:
        logger.info(f"开始更新业务ID: {request.business_ids} 的OCR记录ai_status为0")
        
        records = db.query(OCRModel).filter(
            OCRModel.business_id.in_(request.business_ids),
            OCRModel.is_delete == 0
        ).all()

        if not records:
            logger.info(f"未找到业务ID: {request.business_ids} 的有效OCR记录")
            return OCRUpdateAIStatusResponse(
                message="无有效记录需要更新",
                data=OCRUpdateAIStatusData(updated_count=0)
            )

        for record in records:
            record.ai_status = 0

        db.commit()
        logger.info(f"成功更新{len(records)}条OCR记录的ai_status为0")
        return OCRUpdateAIStatusResponse(
            message="更新成功",
            data=OCRUpdateAIStatusData(updated_count=len(records))
        )

    except Exception as e:
        db.rollback()
        logger.error(f"批量更新ai_status失败，业务ID列表：{request.business_ids}，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/update-ai-status-by-company-ids", response_model=OCRUpdateAIStatusResponse)
async def update_ai_status_by_company_ids(
    request: OCRUpdateAIStatusByCompanyRequest = Body(..., description="公司ID列表请求体"),
    db: Session = Depends(get_db_conn)
):
    """
    根据公司ID列表重置OCR记录的ai_status为0
    - 参数：包含公司ID列表的请求体
    - 返回：更新的记录数量
    """
    try:
        updated_count = await OCRService.update_ai_status_by_company_ids(request.company_ids, db)
        if updated_count == 0:
            return OCRUpdateAIStatusResponse(
                message="无有效记录需要更新",
                data=OCRUpdateAIStatusData(updated_count=0)
            )
        return OCRUpdateAIStatusResponse(
            message="更新成功",
            data=OCRUpdateAIStatusData(updated_count=updated_count)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"根据公司ID更新ai_status失败，公司ID列表：{request.company_ids}，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/statistics", response_model=OCRStatusStatisticsResponse)
async def get_ocr_status_statistics(
    request: OCRStatusStatisticsRequest = Body(..., description="OCR状态统计请求参数"),
    db: Session = Depends(get_db_conn)
):
    """
    统计OCR记录的ai_status分布及电站总数（仅支持公司ID/省份ID筛选）
    - 参数：包含公司/省份ID筛选条件的请求体
    - 返回：各ai_status数量及电站总数
    """
    try:
        # 从服务层获取统计字典
        statistics_dict = await OCRService.get_ai_status_statistics(
            company_ids=request.company_ids,
            province_ids=request.province_ids,
            db=db
        )
        # 将字典转换为Pydantic模型
        statistics = OCRStatusStatisticsData(**statistics_dict)
        return OCRStatusStatisticsResponse(
            message="统计成功",
            data=statistics
        )
    except Exception as e:
        logger.error(f"OCR状态统计失败，错误详情：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")