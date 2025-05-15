from fastapi import APIRouter, HTTPException
from src.configs import ApiConfig
import pymysql
import uuid
import redis
from src.configs.logging_config import setup_logging
import logging
import json

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["OCR任务处理"])


def get_db_connection():
    config = ApiConfig()
    try:
        return pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            db=config.DB_NAME,
            port=config.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.Error as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


def get_redis_client():
    """创建Redis客户端连接"""
    config = ApiConfig()

    # 单机模式
    connection_params = {
        'host': config.REDIS_HOST,
        'port': config.REDIS_PORT,
        'decode_responses': True
    }
    if config.REDIS_PASSWORD:
        connection_params['password'] = config.REDIS_PASSWORD

    return redis.Redis(**connection_params)


async def fetch_ocr_records(limit: int):
    """获取指定数量的OCR记录"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT id, url 
                FROM t_gec_file_ocr_record 
                WHERE (ai_status != 1 OR ai_status is NULL)
                LIMIT %s
            """
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"数据库查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作异常")
    finally:
        connection.close()


async def fetch_ocr_records_by_business_ids(business_ids: list[str]):
    """根据business_ids获取OCR记录"""
    if not business_ids:
        raise HTTPException(status_code=400, detail="业务ID列表不能为空")

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT id, url 
                FROM t_gec_file_ocr_record
                WHERE business_id IN %s
                AND (ai_status != 1 OR ai_status IS NULL)
            """
            cursor.execute(sql, (tuple(business_ids),))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"业务ID查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作异常")
    finally:
        if connection:
            connection.close()


async def store_to_redis(data: dict):
    """存储数据到Redis并返回task_id"""
    try:
        task_id = "vlm_ocr_" + str(uuid.uuid4())
        redis_client = get_redis_client()
        redis_client.set(task_id, json.dumps(data))
        return task_id
    except Exception as e:
        logger.error(f"Redis存储失败: {str(e)}")
        raise HTTPException(status_code=500, detail="缓存服务异常")


@router.post("/process")
async def process_ocr_tasks(limit: int):
    """
    处理OCR任务接口
    - limit: 需要处理的记录数量
    - 返回: 包含task_id的列表
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="请求数量必须大于0")

    try:
        records = await fetch_ocr_records(limit)
        if not records:
            return {"task_ids": [], "message": "没有可处理的记录"}

        # 生成任务ID并存储到Redis
        task_ids = []
        for record in records:
            task_data = {str(record['id']): record['url']}
            task_id = await store_to_redis(task_data)
            task_ids.append(task_id)

        return {"task_ids": task_ids}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/process/by-business-ids")
async def process_ocr_by_business_ids(business_ids: list[str]):
    """
    根据业务ID处理OCR任务接口
    - business_ids: 业务ID列表
    - 返回: 包含task_id的列表
    """
    try:
        records = await fetch_ocr_records_by_business_ids(business_ids)
        if not records:
            return {"task_ids": [], "message": "没有找到对应的OCR记录"}

        task_ids = []
        for record in records:
            task_data = {str(record['id']): record['url']}
            task_id = await store_to_redis(task_data)
            task_ids.append(task_id)

        return {"task_ids": task_ids}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"业务ID处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/process/by-company-ids")
async def process_ocr_by_company_ids(company_ids: list[str]):
    """
    根据公司ID列表处理OCR任务接口
    - company_ids: 公司ID列表
    - 返回: 包含公司ID、任务数量和task_ids的对象
    """
    try:
        # 1. 获取公司对应的业务ID
        business_ids = await fetch_business_ids_by_company_ids(company_ids)
        if not business_ids:
            return {"company_ids": company_ids, "task_count": 0, "task_ids": [], "message": "未找到对应业务ID"}

        # 2. 获取待处理的OCR记录
        records = await fetch_ocr_records_by_business_ids(business_ids)
        if not records:
            return {"company_ids": company_ids, "task_count": 0, "task_ids": [], "message": "未找到待处理的OCR记录"}

        # 3. 生成并存储task_id
        task_ids = []
        for record in records:
            task_data = {str(record['id']): record['url']}
            task_id = await store_to_redis(task_data)
            task_ids.append(task_id)

        return {
            "company_ids": company_ids,
            "task_count": len(task_ids),
            "task_ids": task_ids,
            "message": "任务创建成功"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"公司ID任务处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


async def fetch_business_ids_by_company_ids(company_ids: list[str]):
    """根据公司ID列表获取业务ID列表（power_number对应t_gec_file_ocr_record.business_id）"""
    if not company_ids:
        raise HTTPException(status_code=400, detail="公司ID列表不能为空")

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT power_number  -- 修正为power_number字段（对应t_gec_file_ocr_record.business_id）
                FROM pomp_power_plant_basic 
                WHERE company_id IN %s
            """
            cursor.execute(sql, (tuple(company_ids),))
            result = cursor.fetchall()
            return [row['power_number'] for row in result]  # 返回power_number作为业务ID
    except Exception as e:
        logger.error(f"公司ID查询业务ID失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作异常")
    finally:
        if connection:
            connection.close()
