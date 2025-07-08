# 导入Celery应用、任务装饰器及项目依赖
import asyncio
from src.celery_app import app
from celery import shared_task
from src.configs import ApiConfig
from src.services.ocr_service import OCRService

from src.configs.database import get_db_conn
from src.celery_app.app import CeleryConfig
import logging
from src.configs.redis_config import get_redis_client
from src.services.task_service import TaskService

# 配置Celery任务专用日志记录器
logger = logging.getLogger("celery")

# 在文件顶部添加导入语句


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    try:
        config = CeleryConfig()
        # 只有启用开关打开时才注册任务
        if config.CELERY_FETCH_TASKS_ENABLED:
            logger.info(
                "注册定时任务：获取并发布最新OCR任务（间隔{config.CELERY_FETCH_TASKS_INTERVAL}秒）")
            sender.add_periodic_task(
                config.CELERY_FETCH_TASKS_INTERVAL,
                fetch_and_publish_latest_ocr_tasks.s(
                    limit_count=config.CELERY_FETCH_TASKS_LIMIT),
                name='fetch_and_publish_latest_ocr_tasks'
            )
    except Exception as e:
        logger.error(f"定时任务注册失败：{str(e)}", exc_info=True)
        raise


@shared_task(name='celery_app.tasks.fetch_and_publish_latest_ocr_tasks', bind=True, max_retries=3)
def fetch_and_publish_latest_ocr_tasks(self, limit_count: int = 100):
    """获取最新OCR记录并发布处理任务"""
    try:
        logger.info(f"开始获取最新OCR记录，限制数量：{limit_count}")

        try:
            # 获取数据库连接生成器
            db_generator = get_db_conn()
            db = next(db_generator)
            # 获取Redis客户端生成器
            redis_generator = get_redis_client()
            redis_client = next(redis_generator)
        except StopIteration:
            logger.error("无法获取数据库或Redis连接")
            raise

        # 将异步调用包装在asyncio.run()中
        config = CeleryConfig()
        ai_status = config.CELERY_FETCH_TASKS_AI_STATUS
        # 将-2转换为None，表示不筛选ai_status
        if ai_status == -2:
            ai_status = None
        records = asyncio.run(OCRService.fetch_ocr_records(
            db=db, limit=limit_count, ai_status=ai_status))
        if not records:
            logger.info("未找到需要处理的OCR记录")
            return True

        task_ids = []
        config = ApiConfig()
        for record in records:
            # 跳过已处理或无效记录
            if record.ai_status == 1 or record.is_delete == 1:
                continue

            # 创建任务ID和内容
            task_id = f"{record.id}_{record.business_id}"
            original_urls = record.url.split(',') if record.url else []
            urls = [f"{config.dify.OCR_BASE_URL}{url}" for url in original_urls]

            # 创建并发布任务
            task = TaskService.create_task(
                task_type="ocr_cert_processing",
                content={"urls": urls},
                task_id=task_id
            )
            TaskService.publish_task(task, redis_client)
            task_ids.append(task_id)

        logger.info(f"成功发布{len(task_ids)}个OCR任务")
        return True
    except Exception as e:
        logger.error(f"获取并发布OCR任务失败: {str(e)}", exc_info=True)
        self.retry(exc=e)
    finally:
        # 确保数据库连接生成器完成以释放连接
        try:
            next(db_generator)
        except StopIteration:
            pass
        # 确保Redis连接生成器完成以释放连接
        try:
            next(redis_generator)
        except StopIteration:
            pass
