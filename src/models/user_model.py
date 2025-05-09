from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.configs.database import Base  # 使用绝对导入路径

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    username = Column(String(50), nullable=True, comment='用户名')
    email = Column(String(100), nullable=False, comment='邮箱')
    password = Column(String(100), nullable=False, comment='密码')
    gender = Column(Integer, nullable=True, comment='性别 0-未知 1-男 2-女')
    age = Column(Integer, nullable=True, comment='年龄（允许空值）')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"