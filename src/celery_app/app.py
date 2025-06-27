import os
from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any
from src.configs.logging_config import setup_celery_logging, LogConfig



class CeleryConfig(BaseSettings):
    # 新增任务队列频道配置（与redis_celery_sub对齐）
    CELERY_TASK_QUEUE_CHANNEL: str = "task_queue"
    """Celery 核心配置类（从环境变量或 .env 文件加载配置）"""

    # 消息代理地址（用于任务队列）
    CELERY_BROKER_URL: str = "redis://:123456@localhost:6379/0"
    # 结果存储地址（用于任务结果持久化）
    CELERY_RESULT_BACKEND: str = "redis://:123456@localhost:6379/0"
    # 任务序列化格式（确保跨进程通信数据一致性）
    CELERY_TASK_SERIALIZER: str = "json"
    # 允许接收的内容类型（限制客户端可发送的任务数据格式）
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    # 结果序列化格式（与任务序列化保持一致）
    CELERY_RESULT_SERIALIZER: str = "json"
    # 任务结果过期时间（秒），自动清理旧结果释放存储
    CELERY_RESULT_EXPIRES: int = 3600
    # 时区设置（任务时间展示使用上海时区）
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    # 内部时间存储使用 UTC（避免时区转换问题）
    CELERY_ENABLE_UTC: bool = True

    # 高并发优化配置
    CELERY_WORKER_CONCURRENCY: int = 4  # 每个Worker进程的并发任务数（默认2核机器）
    CELERY_WORKER_AUTOSCALE: str = "8,4"  # 自动扩缩容（最大8个，最小2个Worker进程）
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 2  # 预取任务数量（避免Worker空闲）
    CELERY_TASK_ACKS_LATE: bool = True  # 任务执行完成后再确认（避免Worker崩溃丢失任务）
    CELERY_TASK_QUEUES_MAX_LENGTH: int = 5  # 队列最大长度（需配合Broker配置生效）
    CELERY_TASK_TIME_LIMIT: int = 300  # 单个任务最大执行时间（秒）

    # old
    CELERY_SCAN_TASKS_INTERVAL: int  # 移除默认值，仅声明类型
    # 新增：单次扫描最大任务数（防止单次扫描量过大，无默认值，必填）
    CELERY_SCAN_BATCH_SIZE: int     # 移除默认值，仅声明类型
    # 新增：连接池大小（默认无连接池，频繁创建连接易断开）
    CELERY_BROKER_POOL_LIMIT: int  # 无默认值，从环境变量获取
    # 新增：定时任务开关配置
    CELERY_SCAN_TASKS_ENABLED: bool
    CELERY_FETCH_TASKS_ENABLED: bool
    CELERY_FETCH_TASKS_INTERVAL: int  # 任务执行间隔(秒)
    CELERY_FETCH_TASKS_LIMIT: int    # 任务数量限制

    # 定时任务调度配置（键为任务名称，值为任务详情）
    CELERY_BEAT_SCHEDULE: Dict[str, Any] = {
        # 示例：每小时执行一次的任务（需在 tasks.py 中实现 hourly_task）
        "hourly-task": {
            "task": "celery_app.tasks.hourly_task",  # 任务函数路径
            "schedule": 24*60*60,  # 调度间隔（秒）
        },
        "hourly2-task": {
            "task": "celery_app.test_tasks.hourly2_task",  # 任务函数路径
            "schedule": 24*60*60,  # 调度间隔（秒）
        },
    }

    model_config = SettingsConfigDict(
        env_file=".env",  # 从 .env 文件加载配置
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未定义的额外环境变量（避免配置污染）
    )


# 初始化 Celery 应用实例（参数为当前模块名）
app = Celery(__name__)

# 创建 Celery 配置实例（自动加载环境变量/.env 文件）
config = CeleryConfig()

# 创建日志配置实例（用于 Celery 日志系统初始化）
log_config = LogConfig()

# 设置 Celery 日志（使用自定义日志配置，避免与 FastAPI 日志冲突）
setup_celery_logging(log_config)

# 将配置应用到 Celery 实例（覆盖默认配置）
app.conf.update(
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    task_serializer=config.CELERY_TASK_SERIALIZER,
    accept_content=config.CELERY_ACCEPT_CONTENT,
    result_serializer=config.CELERY_RESULT_SERIALIZER,
    result_expires=config.CELERY_RESULT_EXPIRES,
    timezone=config.CELERY_TIMEZONE,
    enable_utc=config.CELERY_ENABLE_UTC,
    beat_schedule=config.CELERY_BEAT_SCHEDULE,
    worker_hijack_root_logger=False,  # 禁止 Celery 覆盖根日志器（保留 FastAPI 日志）
    worker_redirect_stdouts=False,  # 禁止 Celery 重定向标准输出（避免日志混乱）
    worker_concurrency=config.CELERY_WORKER_CONCURRENCY,  # 并发任务数

    # 新增连接池与重试配置
    broker_pool_limit=config.CELERY_BROKER_POOL_LIMIT,  # 从环境变量获取
    broker_connection_retry_on_startup=True,  # 启动时自动重试连接 Redis
    broker_connection_max_retries=10,         # 最大重试次数

    worker_prefetch_multiplier=config.CELERY_WORKER_PREFETCH_MULTIPLIER,  # 预取倍数
    task_acks_late=config.CELERY_TASK_ACKS_LATE,  # 延迟确认
    worker_autoscale=config.CELERY_WORKER_AUTOSCALE,  # 自动扩缩容
    task_queues_max_length=config.CELERY_TASK_QUEUES_MAX_LENGTH,  # 队列长度限制
    task_time_limit=config.CELERY_TASK_TIME_LIMIT,  # 任务最大执行时间
    # 新增：自定义任务路由（确保任务被正确路由到指定队列）
    task_routes={
        'celery_app.subscriber_tasks.process_task': {'queue': 'subscriber_queue'},
        'celery_app.demo_tasks.process_demo_task': {'queue': 'demo_queue'},
    }
)

app.autodiscover_tasks(packages=["src.celery_app"], related_name="subscriber_tasks")
# app.autodiscover_tasks(packages=['src.celery_app'], related_name='test_tasks')
app.autodiscover_tasks(packages=['src.celery_app'], related_name='ocr_tasks')
