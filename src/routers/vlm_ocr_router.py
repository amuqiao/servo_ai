from fastapi import APIRouter, HTTPException
from typing import Optional
from src.configs import ApiConfig
from src.dify.vlm_ocr import DifyClient
from src.configs.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vlm", tags=["视觉语言模型接口"])

# 初始化Dify客户端
def get_dify_client() -> DifyClient:
    config = ApiConfig()
    try:
        return DifyClient(
            base_url=config.dify.BASE_URL,  # 修改点：通过dify子配置访问
            api_key=config.dify.API_KEY,    # 修改点：通过dify子配置访问
            timeout=config.dify.TIMEOUT     # 修改点：通过dify子配置访问
        )
    except AttributeError as e:
        logger.error(f"Dify配置缺失: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务配置异常，请联系管理员"
        )

@router.post("/process")
async def process_vlm_task(
    image_url: str,
    query: str = "请分析图片内容",
    user_id: Optional[str] = None
):
    """
    VLM图片分析接口
    - image_url: 图片URL（必填）
    - query: 分析指令（默认值：请分析图片内容）
    - user_id: 用户标识（可选）
    """
    if not image_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=400,
            detail="图片URL格式不合法，必须以http/https开头"
        )

    try:
        dify_client = get_dify_client()
        result = dify_client.send_message(
            query=query,
            user=user_id or "anonymous",
            file_source=image_url,
            transfer_method="remote_url"
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Dify服务调用失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"视觉分析服务暂不可用: {str(e)}"
        )