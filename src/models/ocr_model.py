from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, SmallInteger, DECIMAL, Index
from src.configs.database import Base

class OCRModel(Base):
    __tablename__ = 't_gec_file_ocr_record'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='ID')
    status = Column(SmallInteger, nullable=False, comment='状态: 0:未处理 1:处理成功 2:处理失败')  # 调整为 SmallInteger 对应 tinyint
    business_id = Column(String(32), nullable=False, comment='业务ID')
    object_id = Column(String(100), nullable=False, comment='文件存储ID')
    name = Column(String(100), comment='文件名字')
    content = Column(Text, comment='文件扫描内容')
    ai_task_id = Column(String(200), comment='AI任务ID')
    ai_status = Column(SmallInteger, comment='AI状态: 0:未处理 1:处理成功 -1:处理失败')  # 调整为 SmallInteger 对应 tinyint
    ai_content = Column(Text, comment='AI处理内容')
    ai_content_converter = Column(SmallInteger, default=0, comment='ai内容是否转换 0否 1是')  # 新增字段
    url = Column(String(350), comment='文件URL')
    job_id = Column(String(200), comment='任务ID')
    batch_no = Column(String(50), comment='批次号')
    ocr_type = Column(Integer, comment='OCR类型')
    doc_type = Column(String(50), comment='合同类型')
    version = Column(Integer, default=1, comment='版本号')
    record_capacity = Column(DECIMAL(20, 3), comment='备案容量')  # 调整精度为 (20,3)
    remark = Column(String(1000), comment='备注')
    is_delete = Column(SmallInteger, default=0, comment='删除标记: 0:有效 1:删除')  # 调整为 SmallInteger 对应 tinyint
    creator_id = Column(BigInteger, default=0, comment='创建人ID')
    creator = Column(String(50), nullable=False, comment='创建人')
    create_time = Column(DateTime, default=datetime.now, server_default='CURRENT_TIMESTAMP', comment='创建时间')  # 补充 SQL 默认值
    create_by = Column(BigInteger, default=0, comment='更新人ID')
    update_by = Column(String(50), nullable=False, comment='更新人')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, server_default='CURRENT_TIMESTAMP', comment='更新时间')  # 补充 SQL 默认值

    # 新增索引声明
    __table_args__ = (
        Index('idx_business_id_type', 'business_id', 'ocr_type'),
    )

    def __repr__(self):
        return f"<OCRRecord(id={self.id}, batch_no='{self.batch_no}')>"