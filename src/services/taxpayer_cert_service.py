import logging
import re
import ast
import time
import os
from typing import Dict, Any
from src.schemas.taxpayer_cert_schemas import TaxpayerCertResult
from src.configs.config import ApiConfig
from openai import AsyncOpenAI, Timeout
from src.exceptions.taxpayer_cert_exceptions import TaxpayerCertException, TaxpayerCertErrorCode
from src.tools.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class TaxpayerCertService:
    def __init__(self, prompt_filename: str = 'taxpayer_cert_ocr_prompt.txt'):
        self.prompt_filename = prompt_filename
        self.prompt_loader = PromptLoader()

    async def recognize_taxpayer_cert(self, url: str) -> TaxpayerCertResult:
        """纳税人证明OCR识别服务"""
        logger.info(f"开始处理纳税人证明图片: {url}")
        
        # 使用提示词加载器加载提示词
        prompt = self.prompt_loader.load_prompt(self.prompt_filename, file_type='txt')

        try:
            config = ApiConfig()
            api_key = config.dashscope.API_KEY
            if not api_key:
                raise TaxpayerCertException(code=TaxpayerCertErrorCode.OCR_API_KEY_MISSING, message="OCR服务未配置API密钥")

            # 初始化异步OCR客户端
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=config.dashscope.BASE_URL,
            )

            start_time = time.time()
            try:
                # 调用OCR API
                response = await client.chat.completions.create(
                    model="qwen-vl-ocr-latest",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": url,
                                    "min_pixels": 28 * 28 * 4,
                                    "max_pixels": 28 * 28 * 8192
                                },
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                    temperature=0.0,
                    max_tokens=200,
                    timeout=30
                )
                logger.info(f"OCR识别成功，耗时{time.time() - start_time:.2f}秒")
            except Timeout:
                raise TaxpayerCertException(code=TaxpayerCertErrorCode.OCR_TIMEOUT, message="OCR识别超时，请稍后重试")

            # 提取并净化结果
            result_content = response.choices[0].message.content.strip()
            logger.info(f"OCR原始识别结果: {result_content}")

            # 提取JSON部分
            json_match = re.search(r'\{.*\}', result_content, re.DOTALL)
            if not json_match:
                raise TaxpayerCertException(code=TaxpayerCertErrorCode.OCR_PARSE_FAILED, message=f"无法解析OCR结果: {result_content}")
            
            # 解析JSON
            ocr_result = ast.literal_eval(json_match.group())
            
            # 映射到响应模型
            return TaxpayerCertResult(
                credit_code=ocr_result.get("creditCode", ""),
                company_name=ocr_result.get("companyName", ""),
                taxpayer_type=ocr_result.get("taxpayerType", "")
            )
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}", exc_info=True)
            raise TaxpayerCertException(code=TaxpayerCertErrorCode.OCR_SERVICE_ERROR, message=f"纳税人证明识别失败: {str(e)}")