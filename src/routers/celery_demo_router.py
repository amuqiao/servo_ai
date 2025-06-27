from fastapi import APIRouter, Depends, status, Query
from redis import Redis
from src.configs.redis_config import get_redis_client
from src.celery_app.app import CeleryConfig
from src.services.redis_service import RedisBaseService
from src.schemas.response_schema import SuccessResponse, ErrorResponse
from src.schemas.celery_schema import DemoTaskRequest, BatchDemoTaskRequest,GenerateTasksRequest  # 新增Pydantic模型
import uuid
import json  # 新增JSON模块导入
from src.services.task_service import TaskService
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/demo-tasks",
    tags=["Celery 发布任务"],
    responses={404: {"description": "资源未找到", "model": ErrorResponse}, 400: {"description": "参数错误", "model": ErrorResponse}, 500: {"description": "服务器错误", "model": ErrorResponse}}
)

def _generate_task_key() -> str:
    """公共方法：生成符合扫描规则的任务键"""
    return f"demo_task_{str(uuid.uuid4())}"

@router.post("/create", 
             summary="触发单个模拟任务", 
             response_model=SuccessResponse,
             description="向Redis插入单个模拟任务数据，由Celery定时扫描处理")
async def create_pending_task(
    request: DemoTaskRequest,  # 改为Pydantic模型验证
    redis_client: Redis = Depends(get_redis_client)
):
    task_key = _generate_task_key()
    
    success = RedisBaseService.create_key(redis_client, task_key, json.dumps(request.task_data))
    if not success:
        return ErrorResponse(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="任务触发失败", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=None)
    return SuccessResponse(message=f"任务已触发，键：{task_key}", data=None)


@router.post("/queue/single",
             summary="发布单个任务到订阅队列",
             response_model=SuccessResponse)
async def publish_single_task(
    request: DemoTaskRequest,
    redis_client: Redis = Depends(get_redis_client)
):
    config = CeleryConfig()
    if not redis_client.ping():
        raise HTTPException(status_code=500, detail="Redis连接失败")
    
    # 使用TaskService创建并发布任务，支持传递task_id
    try:
        task = TaskService.create_task(
            task_type=request.task_data.get("task_type"),
            content=request.task_data.get("content"),
            task_id=request.task_data.get("task_id")  # 新增传递task_id
        )
        TaskService.publish_task(task, redis_client)
        return SuccessResponse(message=f"任务已发布到订阅队列，ID: {task.task_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/generate_random",
             summary="生成并发布随机任务到订阅队列",
             response_model=SuccessResponse)
async def generate_random_and_publish_tasks(
    request: GenerateTasksRequest,
    redis_client: Redis = Depends(get_redis_client)
):
    config = CeleryConfig()
    if not redis_client.ping():
        raise HTTPException(status_code=500, detail="Redis连接失败")
    
    generated_tasks = []
    for i in range(request.count):
        # 使用TaskService创建任务
        task = TaskService.create_task(
            task_type=request.task_type,
            content=f"随机内容_{i+1}"
        )
        generated_tasks.append(task)
        TaskService.publish_task(task, redis_client)
    
    return SuccessResponse(
        message=f"成功生成并发布'{request.count}'个{request.task_type}类型的随机任务"
    )


@router.post("/queue/batch",
             summary="批量发布任务到订阅队列",
             response_model=SuccessResponse)
async def publish_batch_tasks(
    request: BatchDemoTaskRequest,
    redis_client: Redis = Depends(get_redis_client)
):
    if len(request.task_data_list) < 1:
        raise HTTPException(status_code=400, detail="任务数据列表不能为空")
    config = CeleryConfig()  # 加载Celery配置
    if not redis_client.ping():
        raise HTTPException(status_code=500, detail="Redis连接失败")
    # 循环发布task_data_list中的每个任务数据
    for task_data in request.task_data_list:
        redis_client.publish(
            config.CELERY_TASK_QUEUE_CHANNEL,
            json.dumps(task_data)
        )
    return SuccessResponse(message=f"{len(request.task_data_list)}个任务已批量发布到订阅队列", data=None)