from sqlalchemy.orm import Session
from src.models.user_model import User
from src.configs.database import get_db_conn
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_user(user_data, db: Session):
        try:
            logger.info(f"创建用户: {user_data.username}")
            db_user = User(**user_data.dict(exclude={'password'}))
            db_user.password = user_data.password
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            logger.error(f"用户创建失败: {str(e)}")
            raise

    @staticmethod
    def get_user(user_id: int, db: Session):
        logger.info(f"查询用户ID: {user_id}")
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_users(skip: int, limit: int, db: Session):
        logger.info(f"查询用户列表 offset={skip} limit={limit}")
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(user_id: int, user_data, db: Session):
        logger.info(f"更新用户ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        try:
            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"用户更新失败: {str(e)}")
            raise

    @staticmethod
    def delete_user(user_id: int, db: Session):
        logger.info(f"删除用户ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        try:
            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"用户删除失败: {str(e)}")
            raise