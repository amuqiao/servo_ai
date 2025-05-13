from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import logging

from src.models.ocr_model import OCRModel
from src.configs.database import get_db_conn

router = APIRouter(prefix="/api/ocr-records", tags=["OCR识别结果"])
logger = logging.getLogger(__name__)

class OCRDetailResponse(BaseModel):
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
        orm_mode = True

@router.get("", response_model=list[OCRDetailResponse])
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
        records = db.query(OCRModel).filter(
            OCRModel.business_id.in_(business_ids),
            OCRModel.is_delete == 0
        ).offset((page - 1) * page_size).limit(page_size).all()

        if not records:
            logger.warning(f"未找到业务ID为 {business_ids} 的记录")
            raise HTTPException(status_code=404, detail="未找到相关记录")

        return records
    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{record_id}", response_model=OCRDetailResponse)
async def get_ocr_record(
    record_id: int,
    db: Session = Depends(get_db_conn)
):
    logger.info(f"查询OCR记录ID: {record_id}")
    
    record = db.query(OCRModel).filter(
        OCRModel.id == record_id,
        OCRModel.is_delete == 0
    ).first()

    if not record:
        logger.warning(f"OCR记录不存在: {record_id}")
        raise HTTPException(status_code=404, detail="OCR记录不存在")

    try:
        return record
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")