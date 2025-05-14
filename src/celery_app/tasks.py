from src.celery_app import app
from celery import shared_task
from src.configs import ApiConfig
from urllib.parse import urlparse
import redis
import time
import json
import logging
from datetime import datetime
from src.dify.vlm_ocr import DifyClient
from src.routers.task_processor import get_db_connection, get_redis_client
from src.routers.vlm_ocr_router import get_dify_client
from src.configs.logging_config import setup_logging
import pytz

logger = logging.getLogger("celery")


@shared_task(name='celery_app.tasks.hourly_task')
def hourly_task():

    logger = logging.getLogger("celery.task")  # 使用Celery任务日志器
    logger.info(f"定时任务 hourly_task 执行，时间：{datetime.now().isoformat()}")
    return {"status": "success", "hourly_task_message": "hourly_task 执行完成"}


@shared_task(name='celery_app.tasks.process_task')
def process_task():
    # 示例任务逻辑
    return {"result": "Task processed successfully"}


@shared_task(name='celery_app.tasks.create_redis_key_task')
def create_redis_key_task(task_id: str):
    config = ApiConfig()
    try:
        client = get_redis_client()
        logger.info(f"[Task {task_id}] Storing key with TTL 3600s")
        client.setex(task_id, 3600, f"task_{task_id}_value_{time.time()}")
        logger.info(f"[Task {task_id}] Key stored successfully")
        return True
    except Exception as e:
        logger.error(
            f"[Task {task_id}] Redis operation failed: {str(e)}", exc_info=True)
        return False


def create_redis_key_task2(task_id: str):
    config = ApiConfig()
    try:
        client = get_redis_client()
        logger.info(f"[Task {task_id}] Storing key with TTL 3600s")
        client.setex(task_id, 3600, f"task_{task_id}_value_{time.time()}")
        logger.info(f"[Task {task_id}] Key stored successfully")
        return True
    except Exception as e:
        logger.error(
            f"[Task {task_id}] Redis operation failed: {str(e)}", exc_info=True)
        return False


@shared_task(name='celery_app.tasks.process_ocr_task', bind=True, max_retries=3)
def process_ocr_task(self, task_key):

    logger.info(f"开始处理OCR任务: {task_key}")
    config = ApiConfig()
    try:
        redis_client = get_redis_client()
        data = redis_client.getdel(task_key)

        if not data:
            logger.error(f"空任务数据 {task_key}")
            return

        task_data = json.loads(data)
        record_id, url = next(iter(task_data.items()))
        logger.info(f"获取到OCR任务数据 ID:{record_id} URL:{url}")
        image_url = config.DIDY_OCR_BASE_URL + url
        logger.info(f"构建图片URL: {image_url}")
        try:
            dify_client = get_dify_client()
            logger.info(f"调用Dify服务: ")
            result = dify_client.send_message(
                query="分析图片内容",
                user="anonymous",
                file_source=image_url,
                transfer_method="remote_url"
            )
            answer = json.loads(result['answer'])
        except (RuntimeError, json.JSONDecodeError) as e:
            logger.error(f"Dify服务调用失败: {str(e)}", exc_info=True)
            logger.error(
                f"Dify响应格式异常 原始数据: {json.dumps(result, ensure_ascii=False)}")
            raise self.retry(exc=e, countdown=60)
        except Exception as e:
            logger.error(f"OCR处理意外错误: {str(e)}", exc_info=True)
            logger.error(
                f"Dify响应格式异常 原始数据: {json.dumps(result, ensure_ascii=False)}")
            raise

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """UPDATE t_gec_file_ocr_record 
                        SET ai_task_id = %s, ai_status = 1, ai_content=%s, update_time = %s 
                        WHERE id = %s"""
                    # cursor.execute(sql, (task_key, datetime.now(), record_id))
                    cursor.execute(sql, (f"{task_key}_{self.request.id}", json.dumps(
                        answer, ensure_ascii=False), datetime.now(pytz.timezone('Asia/Shanghai')), record_id))
                    logger.debug(f"数据库更新成功 ID:{record_id}")
                conn.commit()
        except Exception as db_error:
            logger.error(f"数据库操作失败: {str(db_error)}")
            raise

        redis_client.delete(task_key)
        logger.info(f"任务完成并清理: {task_key}")
        return True
    except Exception as e:
        logger.error(f"任务处理失败 {task_key}: {str(e)}", exc_info=True)
        self.retry(countdown=2 ** self.request.retries)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    try:
        logger.info("注册定时任务: %s (间隔 %.1f 秒)", 'scan redis tasks', 60.0)
        sender.add_periodic_task(
            10.0,
            scan_redis_tasks.s(),
            name='scan redis tasks'
        )
    except Exception as e:
        logger.error("定时任务配置失败: %s", str(e), exc_info=True)
        raise


@shared_task(name='celery_app.tasks.scan_redis_tasks')
def scan_redis_tasks():
    try:
        redis_client = get_redis_client()
        cursor = '0'
        total = 0
        while True:
            cursor, keys = redis_client.scan(
                cursor, match='vlm_ocr_*', count=100)
            if keys:
                logger.info(f"扫描到{len(keys)}个待处理任务")
                total += len(keys)
            for key in keys:
                logger.debug(f"分发任务: {key}")
                process_ocr_task.apply_async(args=(key,))
            if cursor == 0:
                break
        if total > 0:
            logger.info(f"本轮共发现{total}个待处理任务")
    except Exception as e:
        logger.error(f"任务扫描异常: {str(e)}", exc_info=True)
