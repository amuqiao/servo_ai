from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models import OCRModel, PompPowerPlantBasic  # 导入OCR模型和关联的电厂基础信息模型
import logging
from datetime import datetime
import pytz
import json
from fastapi import HTTPException  # 补充缺失的HTTPException导入

# 配置日志记录器，指定为celery服务使用
logger = logging.getLogger("celery")

class OCRService:
    @staticmethod
    async def fetch_ocr_records(limit: int, db: Session):
        """
        获取指定数量的待处理OCR记录（AI状态未完成或为空）
        :param limit: 需要获取的记录数量上限
        :param db: 数据库会话对象（通过依赖注入获取）
        :return: OCR记录列表（ORM对象）
        """
        try:
            logger.info(f"开始查询待处理OCR记录，限制数量：{limit}")
            # 使用ORM查询：筛选AI状态不为1或为空的记录，按限制数量获取
            records = db.query(OCRModel).filter(
                or_(OCRModel.ai_status != 1, OCRModel.ai_status == None)
            ).limit(limit).all()
            logger.info(f"成功获取{len(records)}条待处理OCR记录")
            return records
        except Exception as e:
            logger.error(f"查询待处理OCR记录失败，限制数量：{limit}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"数据库查询失败：{str(e)}")

    @staticmethod
    async def fetch_ocr_records_by_business_ids(business_ids: list[str], db: Session):
        """
        根据业务ID列表获取待处理的OCR记录
        :param business_ids: 业务ID列表（如电厂编号）
        :param db: 数据库会话对象
        :return: 匹配的OCR记录列表（ORM对象）
        """
        if not business_ids:
            logger.warning("传入的业务ID列表为空，无法查询OCR记录")
            raise HTTPException(status_code=400, detail="业务ID列表不能为空")
        try:
            logger.info(f"开始根据业务ID查询OCR记录，业务ID数量：{len(business_ids)}")
            # 使用ORM查询：筛选指定业务ID且AI状态未完成的记录
            records = db.query(OCRModel).filter(
                OCRModel.business_id.in_(business_ids),
                or_(OCRModel.ai_status != 1, OCRModel.ai_status == None)
            ).all()
            logger.info(f"成功获取{len(records)}条匹配业务ID的OCR记录")
            return records
        except Exception as e:
            logger.error(f"业务ID查询OCR记录失败，业务ID列表：{business_ids}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"业务ID查询失败：{str(e)}")

    @staticmethod
    async def fetch_business_ids_by_company_ids(company_ids: list[str], db: Session):
        """
        根据公司ID列表获取关联的业务ID（电厂编号）
        :param company_ids: 公司ID列表
        :param db: 数据库会话对象
        :return: 业务ID列表（power_number字段值）
        """
        if not company_ids:
            logger.warning("传入的公司ID列表为空，无法查询业务ID")
            raise HTTPException(status_code=400, detail="公司ID列表不能为空")
        try:
            logger.info(f"开始根据公司ID查询业务ID，公司ID数量：{len(company_ids)}")
            # 关联查询电厂基础表，获取power_number作为业务ID
            results = db.query(PompPowerPlantBasic.power_number).filter(
                PompPowerPlantBasic.company_id.in_(company_ids)
            ).all()
            business_ids = [row.power_number for row in results]
            logger.info(f"成功获取{len(business_ids)}个关联业务ID")
            return business_ids
        except Exception as e:
            logger.error(f"公司ID查询业务ID失败，公司ID列表：{company_ids}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"公司ID查询失败：{str(e)}")

    @staticmethod
    def update_ai_result(record_id: int, ai_task_id: str, ai_content: list, db: Session):
        """
        更新OCR记录的AI处理结果（支持多URL识别结果列表）
        :param record_id: OCR记录ID
        :param ai_task_id: Celery任务ID
        :param ai_content: AI识别结果列表（格式：[{'url': 'xxx', 'content': 'xxx'}, ...]）
        :param db: 数据库会话对象
        :return: 更新后的OCR记录（ORM对象）
        """
        logger.info(f"开始更新OCR记录，记录ID：{record_id}，任务ID：{ai_task_id}")
        ocr_record = db.query(OCRModel).filter(OCRModel.id == record_id).first()
        if not ocr_record:
            logger.error(f"未找到OCR记录，记录ID：{record_id}")
            raise ValueError("OCR记录不存在")
        
        try:
            # 更新字段：任务ID、状态、识别结果（列表转JSON字符串）、更新时间
            ocr_record.ai_task_id = ai_task_id
            ocr_record.ai_status = 1  # 标记为处理成功
            ocr_record.ai_content = json.dumps(ai_content, ensure_ascii=False)  # 保留中文字符
            ocr_record.update_time = datetime.now(pytz.timezone('Asia/Shanghai'))  # 带时区的当前时间
            db.commit()
            db.refresh(ocr_record)  # 刷新对象获取最新数据
            logger.info(f"OCR记录更新成功，记录ID：{record_id}")
            return ocr_record
        except Exception as e:
            db.rollback()  # 异常时回滚事务
            logger.error(f"OCR记录更新失败，记录ID：{record_id}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"记录更新失败：{str(e)}")

    @staticmethod
    def get_ocr_record(record_id: int, db: Session):
        """
        根据记录ID查询单个OCR记录
        :param record_id: OCR记录ID
        :param db: 数据库会话对象
        :return: OCR记录（ORM对象，未找到返回None）
        """
        logger.info(f"开始查询OCR记录，记录ID：{record_id}")
        ocr_record = db.query(OCRModel).filter(OCRModel.id == record_id).first()
        if not ocr_record:
            logger.warning(f"未找到OCR记录，记录ID：{record_id}")
        return ocr_record