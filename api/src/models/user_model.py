from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.configs.database import Base  # 使用绝对导入路径

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(50), nullable=False, comment='姓名')
    gender = Column(Integer, nullable=False, comment='性别 0-未知 1-男 2-女')
    age = Column(Integer, comment='年龄')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"