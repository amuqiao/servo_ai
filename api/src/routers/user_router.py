from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from src.models.user_model import User
from src.configs.database import SessionLocal, get_db_conn
import logging
from src.configs.logging_config import setup_logging
from sqlalchemy import inspect


router = APIRouter(prefix="/api/users", tags=["users"])



setup_logging()

logger = logging.getLogger(__name__)

class InitTableRequest(BaseModel):
    table_name: str
    
class UserResponse(BaseModel):
    message: str

@router.post("/init-table", response_model=UserResponse)
async def init_user_table(
    request: InitTableRequest = Body(...),
):
    logger.info(f"Received request to init table: {request.table_name}")
    db = next(get_db_conn())
    logger.debug(f"成功获取数据库连接: {db}")
    if not request.table_name:
        raise HTTPException(status_code=400, detail="缺少必要参数table_name")
    
    try:
        inspector = inspect(db.get_bind())
        if inspector.has_table(request.table_name):
            return {"message": f"表 {request.table_name} 已存在"}
            
        User.metadata.create_all(bind=db.get_bind(), tables=[User.__table__])
        return {"message": f"表 {request.table_name} 初始化成功"}
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")