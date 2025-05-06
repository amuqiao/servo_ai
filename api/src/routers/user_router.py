from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
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
    
# 更新请求响应模型
class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=3, max_length=50)

class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    gender: int = Field(None, ge=0, le=2)
    age: int = Field(None, ge=0, le=150)

class UserDetailResponse(BaseModel):
    """用户详情响应模型"""
    id: int
    username: str
    email: str
    gender: Optional[int]
    age: Optional[int]
    created_at: datetime
    updated_at: datetime

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserDetailResponse]

class UserResponse(BaseModel):
    """通用响应模型"""
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

# 更新创建接口
@router.post("", response_model=UserDetailResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest = Body(...),
    db: Session = Depends(get_db_conn)
):
    try:
        logger.info(f"创建用户: {user_data.username}")
        db_user = User(**user_data.dict(exclude={'password'}))
        # 密码单独处理（假设有加密逻辑）
        db_user.password = user_data.password  
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"用户创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户创建失败")

@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db_conn)
):
    """获取单个用户详情"""
    logger.info(f"查询用户ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@router.get("", response_model=UserListResponse)
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_conn)
):
    """获取用户列表"""
    logger.info(f"查询用户列表 offset={skip} limit={limit}")
    users = db.query(User).offset(skip).limit(limit).all()
    return {"users": users}

@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest = Body(...),
    db: Session = Depends(get_db_conn)
):
    """更新用户信息"""
    logger.info(f"更新用户ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"用户更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户更新失败")

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db_conn)
):
    """删除用户"""
    logger.info(f"删除用户ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        db.delete(user)
        db.commit()
        return {"message": "用户删除成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"用户删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户删除失败")