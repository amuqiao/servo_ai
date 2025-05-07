from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class InitTableRequest(BaseModel):
    table_name: str

class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=3, max_length=50)

class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    gender: Optional[int] = Field(None, ge=0, le=2)
    age: Optional[int] = Field(None, ge=0, le=150)

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