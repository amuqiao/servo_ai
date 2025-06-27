from redis import Redis
from src.exceptions.redis_exceptions import RedisException, RedisErrorCode

# 重命名为 RedisService（移除冗余的 CRUD 后缀）
class RedisBaseService:
    @staticmethod
    def create_key(redis_client: Redis, key: str, value: str) -> bool:
        """创建键值对"""
        try:
            return redis_client.set(key, value)  # 成功返回True，失败返回False
        except Exception as e:
            # 抛出具体业务异常
            raise RedisException(
                code=RedisErrorCode.KEY_CREATE_FAILED,
                message=f"键 {key} 创建失败: {str(e)}",
                details={"key": key, "error": str(e)}
            )

    @staticmethod
    def get_key(redis_client: Redis, key: str) -> str:
        """获取键值"""
        try:
            value = redis_client.get(key)
            if value is None:
                raise RedisException(
                    code=RedisErrorCode.KEY_NOT_EXIST,
                    message=f"键 {key} 不存在",
                    details={"key": key}
                )
            return value
        except Exception as e:
            raise RedisException(
                code=RedisErrorCode.OPERATION_FAILED,
                message=f"键 {key} 获取失败",
                details={"key": key}
            )

    @staticmethod
    def update_key(redis_client: Redis, key: str, new_value: str) -> bool:
        """更新键值"""
        try:
            return redis_client.set(key, new_value)
        except Exception as e:
            raise RedisException(
                code=RedisErrorCode.KEY_UPDATE_FAILED,
                message=f"键 {key} 更新失败: {str(e)}",
                details={"key": key, "new_value": new_value, "error": str(e)}
            )

    @staticmethod
    def delete_key(redis_client: Redis, key: str) -> int:
        """删除键（返回删除数量）"""
        try:
            return redis_client.delete(key)  # 0（未删除）或1（已删除）
        except Exception as e:
            raise RedisException(
                code=RedisErrorCode.KEY_DELETE_FAILED,
                message=f"键 {key} 删除失败: {str(e)}",
                details={"key": key, "error": str(e)}
            )

    @staticmethod
    def scan_keys(redis_client: Redis, match_pattern: str = "*", count: int = 100) -> list[str]:
        """
        通用扫描键方法（替代原RedisTaskService的scan_ocr_tasks）
        :param redis_client: Redis客户端实例
        :param match_pattern: 匹配模式（如"demo_task_*"）
        :param count: 每次扫描的最大返回数
        :return: 匹配的键列表（字符串形式）
        """
        try:
            cursor = '0'
            keys = []
            while True:
                cursor, batch = redis_client.scan(cursor=cursor, match=match_pattern, count=count)
                keys.extend(batch)
                if cursor == 0:  # 扫描完成
                    break
            # 修复：仅对字节类型的键解码，字符串类型直接保留（调整判断顺序避免误操作）
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            raise RedisException(
                code=RedisErrorCode.OPERATION_FAILED,
                message=f"扫描键失败: {str(e)}",
                details={"match_pattern": match_pattern, "error": str(e)}
            )

    @staticmethod
    def get_and_delete_key(redis_client: Redis, key: str) -> str:
        """
        原子操作：获取并删除键（替代原RedisTaskService的get_and_delete_task_data）
        :param redis_client: Redis客户端实例
        :param key: 目标键
        :return: 键对应的值（字符串形式，无值返回空字符串）
        """
        try:
            # value = redis_client.getdel(key)  # 原子操作
            value = redis_client.get(key)  # 先获取值
            redis_client.delete(key)  # 再删除键
            return value

        except Exception as e:
            raise RedisException(
                code=RedisErrorCode.OPERATION_FAILED,
                message=f"获取并删除键失败: {str(e)}",
                details={"key": key, "error": str(e)}
            )