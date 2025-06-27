import json
import logging
from typing import Dict, Any
from src.tools.pdf2image import PdfToImageConverter
from src.tools.ocr_cert import OCRCertInfoExtractor
from src.services.ocr_service import OCRService
from io import BytesIO
from src.services.tasks.base_task import BaseTask
from src.configs.database import get_db_conn
from fastapi import Depends
from sqlalchemy.orm import Session

# 初始化任务专用日志器
logger = logging.getLogger("celery")

class OCRCertTask(BaseTask):
    task_type = "ocr_cert_processing"

    def __init__(self, task_id: str, content: Dict[str, Any]):
        super().__init__(task_id, content)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OCRCertTask':
        return cls(
            task_id=data["task_id"],
            content=data["content"]
        )

    def parse_content(self) -> Dict[str, Any]:
        # 解析逻辑实现
        return self.content

    def image_urls_to_ocr_results(self, urls: list, workers: int = 2):
        """
        从图片URL列表获取OCR识别结果

        :param urls: 图片URL列表
        :param workers: 并行工作线程数
        :return: OCR识别结果的字典列表
        """
        # 初始化OCR信息提取器
        ocr_extractor = OCRCertInfoExtractor()
        # 设置工作线程数
        ocr_extractor.max_workers = workers
        # 从URL列表获取OCR结果
        return ocr_extractor.from_urls(urls)

    def pdf_urls_to_ocr_results(self, pdf_urls: list, scale_factor: float = 2.0, workers: int = 2):
        """
        从 PDF URL 列表获取 OCR 识别结果

        :param pdf_urls: PDF 文件 URL 列表
        :param scale_factor: 缩放倍数，默认为初始化时的设置
        :param workers: 并行工作线程数，默认为初始化时的设置
        :return: OCR 识别结果的字典列表
        """
        # 初始化 PDF 转图片转换器
        pdf_converter = PdfToImageConverter(scale_factor=scale_factor, workers=workers)
        # 初始化 OCR 信息提取器
        ocr_extractor = OCRCertInfoExtractor()

        # 将 PDF URL 列表转换为图片文件流列表
        image_streams = pdf_converter.urls_to_image_streams(pdf_urls, scale_factor, workers)

        ocr_results = []
        # 对每个图片文件流进行 OCR 识别
        for image_stream in image_streams:
            try:
                # 将字节流转换为文件流对象
                with BytesIO(image_stream) as img_buffer:
                    # 进行 OCR 识别
                    result = ocr_extractor.from_file(img_buffer)
                ocr_results.append(result)
            except Exception as e:
                print(f"OCR 识别出错: {str(e)}")

        return ocr_results

    # 修改process方法定义，移除Depends依赖注入
    def process(self):
        # 手动获取数据库会话
        db = next(get_db_conn())
        try:
            logger.info(f"开始处理通知任务，ID: {self.task_id}，内容: {self.content}")

            # 获取URL列表并分类
            urls = self.content.get("urls", [])
            pdf_urls = [url.strip() for url in urls if url.strip().lower().endswith('.pdf')]
            image_urls = [url.strip() for url in urls if not url.strip().lower().endswith('.pdf')]
    
            # 分别处理不同类型的URL
            ocr_results = []
            if pdf_urls:
                ocr_results.extend(self.pdf_urls_to_ocr_results(pdf_urls))
            if image_urls:
                ocr_results.extend(self.image_urls_to_ocr_results(image_urls))
            json_str = json.dumps(ocr_results, ensure_ascii=False)
            logger.info(f"OCRCertTask识别结果: {json_str}")
            # 新增：验证OCR结果是否包含错误
            has_error = False
            for result in ocr_results:
                if isinstance(result, dict) and 'error' in result:
                    has_error = True
                    logger.error(f"OCR识别失败: {result['error']}")
                    break
            
            try:
                # 从task_id解析record_id
                record_id = int(self.task_id.split('_')[0])
                # 根据是否有错误设置ai_status
                ai_status = -1 if has_error else 1
                OCRService.update_ai_result(record_id, self.task_id, self.convert_data1_to_data2_structure(ocr_results), ai_status, db)
            except Exception as e:
                logger.error(f"OCR结果更新失败: {str(e)}")
                raise
    
            # 实际业务处理逻辑
            processed_result = {"status": "notified", "content": self.content, "ocr_results": ocr_results}

            return {
                "status": "success",
                "task_id": self.task_id,
                "result": processed_result
            }
        finally:
            # 确保数据库会话正确关闭
            db.close()
    
    @staticmethod
    def convert_data1_to_data2_structure(data):
        # 数据结构转换说明：
        # 1. 输入数据(data)为列表形式，包含一个或多个备案信息字典
        # 2. 输出为列表形式，每个元素包含两个字段：
        #    - url: 字符串类型，此处填充为空字符串
        #    - content: 对象类型，保留原始数据项的完整结构
        # 3. 转换逻辑：遍历输入数据列表，为每个元素创建新的字典包装
        return [{
            "url": "",  # URL字段设置为空字符串
            "content": item  # content字段保留原始数据项的完整结构
        } for item in data]
        
        
        
        


