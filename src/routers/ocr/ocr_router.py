from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from src.models.ocr_model import OCRModel
from src.configs.database import get_db_conn

router = APIRouter(prefix="/api/ocr-records", tags=["OCR"])
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