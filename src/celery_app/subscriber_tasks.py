import redis
import json
import logging
from src.celery_app import app
from src.configs.redis_config import get_redis_client
from src.celery_app.app import CeleryConfig
from src.services.task_service import TaskService

# 初始化Celery任务专用日志器
logger = logging.getLogger("celery")

@app.on_after_configure.connect
def start_redis_subscriber(sender, **kwargs):
    """Celery配置完成后启动Redis订阅器"""
    from src.configs.redis_config import get_redis_client
    redis_generator = get_redis_client()
    redis_client = next(redis_generator)
    try:
        redis_client.ping()
        logger.info("Redis连接测试成功")
    except redis.RedisError as e:
        logger.error(f"Redis连接失败: {str(e)}", exc_info=True)
        raise
    logger.info("Redis连接成功，等待任务...")
    config = CeleryConfig()  # 加载Celery配置
    pubsub = redis_client.pubsub()
    pubsub.subscribe(config.CELERY_TASK_QUEUE_CHANNEL)

    def listen_for_messages():
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    task_data = json.loads(message['data'])
                    logger.info(f"收到任务: {task_data.get('task_type')}")
                    
                    process_task.delay(task_data)
                except json.JSONDecodeError:
                    app.logger.error("JSON解析失败")

    # 启动后台线程监听消息
    import threading
    threading.Thread(target=listen_for_messages, daemon=True).start()
    
@app.task(bind=True, default_retry_delay=300, max_retries=5)
def process_task(self, task_data):
    try:
        # 使用TaskService解析任务
        logger.info(f"TaskService解析任务")
        task = TaskService.parse_task(task_data)
        worker_id = self.request.hostname
        logger.info(f"Worker {worker_id} 领取任务，类型：{task.task_type}，ID：{task.task_id}")
        
        # 调用任务自身的process方法
        result = task.process()
        return result
    except Exception as e:
        logger.error(f"任务处理失败: {str(e)}", exc_info=True)
        self.retry(exc=e)

