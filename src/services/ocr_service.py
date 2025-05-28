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
    async def _base_fetch_ocr_records(db: Session, business_ids: list[str] = None, limit: int = None):
        """
        基础OCR记录查询方法（抽象公共查询逻辑）
        :param db: 数据库会话
        :param business_ids: 业务ID列表（可选过滤条件）
        :param limit: 限制数量（可选）
        :return: OCR记录列表
        """
        # 公共条件：AI状态未完成或为空
        query = db.query(OCRModel).filter(
            or_(OCRModel.ai_status != 1, OCRModel.ai_status == None)
        )

        # 业务ID过滤（可选）
        if business_ids:
            query = query.filter(OCRModel.business_id.in_(business_ids))
        
        # 数量限制（可选）
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()

    @staticmethod
    async def fetch_ocr_records(limit: int, db: Session):
        """获取指定数量的待处理OCR记录（调用基础查询方法）"""
        return await OCRService._base_fetch_ocr_records(db, limit=limit)

    @staticmethod
    async def fetch_ocr_records_by_business_ids(business_ids: list[str], db: Session):
        """根据业务ID列表获取待处理OCR记录（调用基础查询方法）"""
        if not business_ids:
            logger.warning("传入的业务ID列表为空，无法查询OCR记录")
            raise HTTPException(status_code=400, detail="业务ID列表不能为空")
        return await OCRService._base_fetch_ocr_records(db, business_ids=business_ids)

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
    async def fetch_ocr_records_by_company_ids(company_ids: list[str], db: Session):
        """
        根据公司ID列表获取关联的待处理OCR记录（整合公司ID→业务ID→记录的流程）
        :param company_ids: 公司ID列表
        :param db: 数据库会话对象
        :return: 关联的OCR记录列表（ORM对象）
        """
        if not company_ids:
            logger.warning("传入的公司ID列表为空，无法查询OCR记录")
            raise HTTPException(status_code=400, detail="公司ID列表不能为空")
        
        # 步骤1：获取公司关联的业务ID
        business_ids = await OCRService.fetch_business_ids_by_company_ids(company_ids, db)
        if not business_ids:
            logger.info("未找到公司ID关联的业务ID")
            return []
        
        # 步骤2：根据业务ID获取待处理记录
        records = await OCRService.fetch_ocr_records_by_business_ids(business_ids, db)
        return records

    @staticmethod
    def update_ai_result(record_id: int, ai_task_id: str, ai_content: list, ai_status: int, db: Session):  # 新增ai_status参数
        """
        更新OCR记录的AI处理结果（支持多URL识别结果列表）
        """
        logger.info(f"开始更新OCR记录，记录ID：{record_id}，任务ID：{ai_task_id}")
        ocr_record = db.query(OCRModel).filter(OCRModel.id == record_id).first()
        if not ocr_record:
            logger.error(f"未找到OCR记录，记录ID：{record_id}")
            raise ValueError("OCR记录不存在")
        
        try:
            ocr_record.ai_task_id = ai_task_id
            ocr_record.ai_status = ai_status  # 使用传入的状态值
            ocr_record.ai_content = json.dumps(ai_content, ensure_ascii=False)
            ocr_record.update_time = datetime.now(pytz.timezone('Asia/Shanghai'))
            db.commit()
            db.refresh(ocr_record)
            logger.info(f"OCR记录更新成功，记录ID：{record_id}")
            return ocr_record
        except Exception as e:
            db.rollback()  # 异常时回滚事务
            logger.error(f"OCR记录更新失败，记录ID：{record_id}，错误详情：{str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"记录更新失败：{str(e)}")

    @staticmethod
    def check_need_ocr(record_id: int, db: Session) -> bool:
        """
        检查OCR记录是否需要执行识别（ai_status不为1时需要）
        :param record_id: OCR记录ID
        :param db: 数据库会话对象
        :return: 需要识别返回True，否则返回False
        """
        logger.debug(f"检查OCR记录是否需要识别，记录ID：{record_id}")
        ocr_record = OCRService.get_ocr_record(record_id, db)
        if not ocr_record:
            logger.error(f"未找到OCR记录，记录ID：{record_id}")
            raise ValueError("OCR记录不存在")
        return ocr_record.ai_status != 1  # ai_status=1时无需处理

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