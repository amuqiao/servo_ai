# 导入Celery应用、任务装饰器及项目依赖
from src.celery_app import app
from celery import shared_task
from src.configs import ApiConfig
from src.services.ocr_service import OCRService
from src.services.redis_task_service import RedisTaskService  # Redis任务操作服务
from src.routers.vlm_ocr_router import get_dify_client  # 获取Dify OCR客户端
from src.configs.logging_config import setup_logging
from src.configs.database import get_db_conn  # 数据库连接生成器
import json
import logging
import pytz
from typing import Dict, Any  # 类型提示支持

# 配置Celery任务专用日志记录器
logger = logging.getLogger("celery")

@shared_task(name='celery_app.tasks.process_ocr_task', bind=True, max_retries=3)
def process_ocr_task(self, task_key: str) -> bool:
    """
    Celery OCR处理任务：从Redis获取任务数据，调用OCR服务识别，更新数据库结果
    :param task_key: Redis中的任务键（唯一标识任务）
    :return: 任务处理是否成功（True/False）
    """
    logger.info(f"开始处理OCR任务，任务键：{task_key}")
    config = ApiConfig()  # 加载项目配置
    db = None  # 初始化数据库会话变量

    try:
        # 1. 从Redis获取并删除任务数据（原子操作）
        logger.debug(f"尝试从Redis获取任务数据，任务键：{task_key}")
        data = RedisTaskService.get_and_delete_task_data(task_key)
        if not data:
            logger.error(f"任务数据为空，任务键：{task_key}")
            return False

        # 2. 解析任务数据（格式：{record_id: [url1, url2, ...]}）
        logger.debug(f"解析任务数据，任务键：{task_key}")
        task_data = json.loads(data)
        record_id_str, urls = next(iter(task_data.items()))  # 提取记录ID和URL列表
        record_id = int(record_id_str)
        logger.info(f"成功获取OCR任务数据，记录ID：{record_id}，待处理URL数量：{len(urls)}")

        # 获取数据库会话（提前获取用于状态检查）
        db_generator = get_db_conn()
        db = next(db_generator)
        try:
            # 新增：检查是否需要执行OCR识别（ai_status=1时跳过）
            need_ocr = OCRService.check_need_ocr(record_id, db)
            if not need_ocr:
                logger.info(f"OCR记录已处理成功，跳过识别，记录ID：{record_id}")
                RedisTaskService.delete_task_key(task_key)  # 清理任务键
                logger.info(f"任务提前完成并清理，任务键：{task_key}，记录ID：{record_id}")
                return True

            # 3. 调用Dify客户端处理每个URL的OCR识别（仅当需要处理时执行）
            dify_client = get_dify_client()
            results = []
            all_url_success = True  # 跟踪所有URL是否处理成功
            for url in urls:
                try:
                    logger.debug(f"开始处理URL：{url}，记录ID：{record_id}")
                    # 调用Dify API识别图片内容
                    result = dify_client.send_message(
                        query="分析图片内容",
                        user="anonymous",
                        file_source=config.DIDY_OCR_BASE_URL + url,
                        transfer_method="remote_url"
                    )
                    answer = json.loads(result['answer'])  # 解析识别结果
                    results.append({"url": url, "content": answer})
                    logger.info(f"URL处理成功，URL：{url}，记录ID：{record_id}")
                except Exception as e:
                    all_url_success = False  # 任意URL失败则标记整体失败
                    logger.error(f"URL处理失败，URL：{url}，记录ID：{record_id}，错误详情：{str(e)}", exc_info=True)
                    break  # 失败时终止遍历，不再处理后续URL

            # 4. 更新数据库OCR结果（传递实际状态）
            logger.debug(f"准备更新数据库，记录ID：{record_id}，任务键：{task_key}")
            ai_status = 1 if all_url_success else -1
            OCRService.update_ai_result(
                record_id=record_id,
                ai_task_id=f"{task_key}_{self.request.id}",
                ai_content=results,
                ai_status=ai_status,  # 新增参数传递状态
                db=db
            )
            db.commit()
            logger.info(f"数据库更新成功，记录ID：{record_id}，任务键：{task_key}")
        finally:
            db.close()  # 手动关闭会话
            next(db_generator, None)  # 执行生成器清理逻辑（释放连接池资源）

        # 5. 清理Redis任务键（避免重复处理）
        RedisTaskService.delete_task_key(task_key)
        logger.info(f"任务完成并清理，任务键：{task_key}，记录ID：{record_id}")
        return True

    except Exception as e:
        logger.error(f"任务处理整体失败，任务键：{task_key}，错误详情：{str(e)}", exc_info=True)
        # 触发重试（最大重试次数由max_retries=3控制）
        self.retry(countdown=2 ** self.request.retries)
        return False  # 确保所有分支有返回值

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    注册Celery定时任务：定期扫描Redis中的OCR待处理任务
    """
    try:
        config = ApiConfig()  # 加载配置
        logger.info(f"注册定时任务：扫描Redis OCR任务（间隔{config.CELERY_SCAN_TASKS_INTERVAL}秒）")
        sender.add_periodic_task(
            config.CELERY_SCAN_TASKS_INTERVAL,  # 使用环境变量配置的间隔时间
            scan_redis_tasks.s(),  # 绑定扫描任务
            name='scan redis tasks'  # 任务名称
        )
    except Exception as e:
        logger.error(f"定时任务注册失败，错误详情：{str(e)}", exc_info=True)
        raise  # 抛出异常避免静默失败

@shared_task(name='celery_app.tasks.scan_redis_tasks')
def scan_redis_tasks():
    """
    扫描Redis中的OCR待处理任务键，并分发给process_ocr_task处理
    """
    try:
        logger.debug("开始扫描Redis中的OCR待处理任务")
        tasks = RedisTaskService.scan_ocr_tasks()  # 获取所有匹配的任务键（模式：vlm_ocr_*）
        if tasks:  # 仅当有任务时记录INFO日志
            logger.info(f"扫描到{len(tasks)}个待处理OCR任务键")
            for key in tasks:
                logger.debug(f"分发任务键：{key} 到OCR处理任务")
                process_ocr_task.apply_async(args=(key,))  # 异步执行OCR处理任务
        else:
            logger.debug("未扫描到待处理的OCR任务键")  # 无任务时记录DEBUG日志
    except Exception as e:
        logger.error(f"任务扫描异常，错误详情：{str(e)}", exc_info=True)
