import logging
import re
import ast
import time
from typing import Dict, Any
from src.schemas.taxpayer_cert_schemas import TaxpayerCertResult
from src.configs.config import ApiConfig
from openai import AsyncOpenAI, Timeout
from src.exceptions.taxpayer_cert_exceptions import TaxpayerCertException, TaxpayerCertErrorCode

logger = logging.getLogger(__name__)

class TaxpayerCertService:
    @staticmethod
    async def recognize_taxpayer_cert(url: str) -> TaxpayerCertResult:
        """纳税人证明OCR识别服务"""
        logger.info(f"开始处理纳税人证明图片: {url}")
        
        # 加载OCR提示词
        prompt = """
        请从这张企业税务信息界面截图中，提取公司名称、小规模纳税人标识（这里是‘小规模纳税人’文字本身）、统一社会信用代码，
        将这些信息整理成JSON格式返回，JSON结构包含'companyName'（对应公司名称）、'taxpayerType'（对应小规模纳税人）、
        'creditCode'（对应统一社会信用代码）三个字段。
        示例预期返回（基于图中内容）：
        {
        "companyName": "重庆足鑫光伏科技有限公司",
        "taxpayerType": "小规模纳税人",
        "creditCode": "91500111MADAFDA278"
        }
        """.strip()
        
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