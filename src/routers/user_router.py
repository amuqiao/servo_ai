# 优化后的import结构（标准库→第三方库→本地模块）
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy import inspect
from sqlalchemy.orm import Session
import logging

# 本地模块导入
from src.models.user_model import User
from src.configs.database import get_db_conn
from src.configs.logging_config import setup_logging
from src.validators.user_validators import (
    InitTableRequest,
    UserCreateRequest,
    UserUpdateRequest,
    UserDetailResponse,
    UserListResponse,
    UserResponse
)

# 初始化路由实例
router = APIRouter(prefix="/api/users", tags=["users"])

# 配置日志系统
setup_logging()
logger = logging.getLogger(__name__)

@router.post("/init-table", response_model=UserResponse)
async def init_user_table(
    request: InitTableRequest = Body(...),
    db: Session = Depends(get_db_conn)  # 改为依赖注入模式
):
    """初始化用户表（使用数据库连接池）"""
    logger.info(f"初始化用户表请求: {request.table_name}")
    
    if not request.table_name:
        raise HTTPException(status_code=400, detail="缺少必要参数table_name")

    try:
        # 检查表是否存在
        inspector = inspect(db.get_bind())
        if inspector.has_table(request.table_name):
            return {"message": f"表 {request.table_name} 已存在"}
            
        # 创建表操作（自动事务管理）
        User.metadata.create_all(bind=db.get_bind(), tables=[User.__table__])
        return {"message": f"表 {request.table_name} 初始化成功"}
        
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")
    finally:
        db.close()  # 确保连接归还连接池

# 更新创建接口
@router.post("", response_model=UserDetailResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest = Body(...),
    db: Session = Depends(get_db_conn)
):
    from src.services.user_service import UserService

    try:
        return UserService.create_user(user_data, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail="用户创建失败")

@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db_conn)
):
    """获取单个用户详情"""
    logger.info(f"查询用户ID: {user_id}")
    from src.services.user_service import UserService
    if (user := UserService.get_user(user_id, db)) is None:
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
    from src.services.user_service import UserService
    logger.info(f"查询用户列表 offset={skip} limit={limit}")
    return {"users": UserService.get_users(skip, limit, db)}

@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest = Body(...),
    db: Session = Depends(get_db_conn)
):
    """更新用户信息"""
    logger.info(f"更新用户ID: {user_id}")
    from src.services.user_service import UserService
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        return UserService.update_user(user_id, user_data, db)
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
    from src.services.user_service import UserService
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        UserService.delete_user(user_id, db)
        return {"message": "用户删除成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"用户删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail="用户删除失败")