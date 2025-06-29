# 导入Celery应用、任务装饰器及项目依赖
import asyncio
from src.celery_app import app
from celery import shared_task
from src.configs import ApiConfig
from src.services.ocr_service import OCRService
from src.services.redis_task_service import RedisTaskService  # Redis任务操作服务
from src.routers.vlm_ocr_router import get_dify_client  # 获取Dify OCR客户端
from src.configs.logging_config import setup_logging
from src.configs.database import get_db_conn  # 数据库连接生成器
from src.celery_app.app import CeleryConfig  # 新增：导入Celery配置类
import json
import logging
import pytz
from typing import Dict, Any  # 类型提示支持
from src.configs.redis_config import get_redis_client
from src.services.task_service import TaskService

# 配置Celery任务专用日志记录器
logger = logging.getLogger("celery")

# 在文件顶部添加导入语句


@shared_task(name='celery_app.tasks.process_ocr_task', bind=True, max_retries=3)
def process_ocr_task(self, task_key: str) -> bool:
    """
    Celery OCR处理任务：从Redis获取任务数据，调用OCR服务识别，更新数据库结果
    """
    logger.info(f"[OCR任务处理] 开始处理OCR任务，任务键：{task_key}")  # 关键入口日志保留
    config = ApiConfig()
    db = None

    try:
        data = RedisTaskService.get_and_delete_task_data(task_key)
        if not data:
            logger.error(f"任务数据为空，任务键：{task_key}")  # 关键错误日志保留（移除冗余的{data}）
            return False

        task_data = json.loads(data)
        record_id_str, urls = next(iter(task_data.items()))
        record_id = int(record_id_str)
        logger.info(
            f"获取到OCR任务数据（记录ID：{record_id}，待处理URL数：{len(urls)}）")  # 关键信息保留

        db_generator = get_db_conn()
        db = next(db_generator)
        try:
            need_ocr = OCRService.check_need_ocr(record_id, db)
            if not need_ocr:
                # 关键清理日志保留
                logger.info(f"OCR记录已处理成功（记录ID：{record_id}），清理任务键：{task_key}")
                RedisTaskService.delete_task_key(task_key)
                return True

            dify_client = get_dify_client()
            results = []
            all_url_success = True
            for url in urls:
                try:
                    # 降级为debug（原info）
                    logger.debug(f"开始处理URL：{url}，记录ID：{record_id}")
                    # 调用Dify API识别图片内容
                    result = dify_client.send_message(
                        query="分析图片内容",
                        user="anonymous",
                        file_source=config.dify.OCR_BASE_URL + url,
                        transfer_method="remote_url"
                    )
                    answer = json.loads(result['answer'])  # 解析识别结果
                    results.append({"url": url, "content": answer})
                    # 降级为debug（原info）
                    logger.debug(f"URL处理成功，URL：{url}，记录ID：{record_id}")
                except Exception as e:
                    all_url_success = False  # 任意URL失败则标记整体失败
                    logger.error(
                        # 关键错误保留
                        f"URL处理失败（记录ID：{record_id}）：URL={url}，错误详情：{str(e)}", exc_info=True)
                    break  # 失败时终止遍历，不再处理后续URL

            # 更新数据库OCR结果
            logger.debug(f"[OCR任务处理] 准备更新数据库（记录ID：{record_id}）")  # 降级为debug（原info）
            ai_status = 1 if all_url_success else -1
            OCRService.update_ai_result(
                record_id=record_id,
                ai_task_id=f"{task_key}_{self.request.id}",
                ai_content=results,
                ai_status=ai_status,
                db=db
            )
            db.commit()
            logger.info(f"数据库更新成功（记录ID：{record_id}）")  # 关键成功日志保留

        finally:
            db.close()
            next(db_generator, None)

        RedisTaskService.delete_task_key(task_key)
        logger.info(f"OCR任务完成（记录ID：{record_id}，任务键：{task_key}）")  # 关键完成日志保留
        return True

    except Exception as e:
        logger.error(f"任务处理失败（任务键：{task_key}）：{str(e)}",
                     exc_info=True)  # 关键异常日志保留
        self.retry(countdown=2 ** self.request.retries)
        return False


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    try:
        config = CeleryConfig()
        if config.CELERY_SCAN_TASKS_ENABLED:
            logger.info(
                f"注册定时任务：扫描Redis任务（间隔{config.CELERY_SCAN_TASKS_INTERVAL}秒）")
            sender.add_periodic_task(
                config.CELERY_SCAN_TASKS_INTERVAL,
                scan_redis_tasks.s(),
                name='scan redis tasks'
            )
        # 新增：注册获取并发布最新OCR任务的定时任务
        logger.info("注册定时任务：获取并发布最新OCR任务（间隔60秒）")
        # 修改任务调度配置
        # 新增：只有启用开关打开时才注册任务
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


@shared_task(name='celery_app.tasks.scan_redis_tasks')
def scan_redis_tasks():
    """扫描Redis中的OCR待处理任务键（优化版）"""
    try:
        config = CeleryConfig()
        batch_size = config.CELERY_SCAN_BATCH_SIZE
        logger.debug(f"开始扫描Redis OCR任务（批量大小：{batch_size}）")  # 降级为debug（原info）

        tasks = RedisTaskService.scan_ocr_tasks(max_count=batch_size)

        if tasks:
            # 关键扫描结果保留
            logger.info(f"扫描到{len(tasks)}个待处理OCR任务（限制{batch_size}条）")
            for key in tasks:
                if RedisTaskService.check_task_exists(key):
                    logger.debug(f"分发任务键：{key}")  # 降级为debug（原info）
                    process_ocr_task.apply_async(args=(key,))
                else:
                    logger.debug(f"任务键已不存在，跳过：{key}")  # 降级为debug（原info）
        else:
            logger.debug("未扫描到待处理OCR任务")  # 降级为debug（原info）

    except Exception as e:
        logger.error(f"任务扫描异常：{str(e)}", exc_info=True)


@shared_task(name='celery_app.tasks.fetch_and_publish_latest_ocr_tasks', bind=True, max_retries=3)
def fetch_and_publish_latest_ocr_tasks(self, limit_count: int = 100):
    """获取最新OCR记录并发布处理任务"""
    try:
        logger.info(f"开始获取最新OCR记录，限制数量：{limit_count}")

        try:
            # 获取数据库连接
            db = next(get_db_conn())
            # 获取Redis客户端，从生成器中获取实际客户端实例
            redis_generator = get_redis_client()
            redis_client = next(redis_generator)
        except StopIteration:
            logger.error("无法获取数据库连接")
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
