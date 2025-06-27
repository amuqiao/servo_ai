import requests
import json
import logging
from typing import Optional, Union

logger = logging.getLogger("celery")

class DifyClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 180):
        self.timeout = timeout
        self.base_url = base_url.rstrip('/')  # 保持原逻辑去除末尾斜杠
        self.api_key = api_key
        self.default_headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'DifyClient/2.0',
            'Accept': 'application/json'
        }
        logger.info(f"DifyClient 初始化完成，base_url: {self.base_url}")  # 初始化日志

    def upload_file(self, file_path: str, user: str) -> str:
        """上传本地文件并返回文件ID"""
        logger.info(f"开始上传文件，路径: {file_path}，用户: {user}")  # 上传开始日志
        upload_url = f"{self.base_url}/files/upload"  # 调整路径，移除重复的/v1

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (
                    file_path.split('/')[-1],  # 文件名
                    f,  # 文件对象
                    'image/jpeg'  # 添加明确的MIME类型 ← 这是关键修复
                )}
                data = {'user': user}

                response = requests.post(
                    upload_url,
                    headers={k: v for k, v in self.default_headers.items()
                             if k != 'Content-Type'},
                    files=files,
                    data=data
                )

                if response.status_code == 201:
                    file_id = response.json()['id']
                    logger.info(f"文件上传成功，文件ID: {file_id}")  # 上传成功日志
                    return file_id
                logger.error(
                    # 上传失败日志
                    f"上传失败，状态码: {response.status_code}，响应内容: {response.text}")
                raise Exception(f"上传失败: {response.text}")

        except Exception as e:
            logger.error(f"文件上传错误: {str(e)}")  # 异常日志
            raise RuntimeError(f"文件上传错误: {str(e)}")

    def send_message(
        self,
        query: str,
        user: str,
        file_source: Union[str, bytes],
        transfer_method: str = "remote_url",
        response_mode: str = "blocking",
        conversation_id: Optional[str] = None
    ) -> dict:
        """发送带文件引用的聊天消息"""
        logger.info(
            # 消息发送开始日志
            f"准备发送消息，查询内容: {query}，用户: {user}，传输方式: {transfer_method}")
        file_data = self._prepare_file_data(file_source, transfer_method, user)

        payload = {
            "inputs": {"file": file_data},
            "query": query,
            "response_mode": response_mode,
            "user": user,
            "files": [file_data]
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id
            logger.info(f"使用现有对话ID: {conversation_id}")  # 对话ID日志

        return self._post_message(payload)

    def _prepare_file_data(self, file_source: Union[str, bytes], method: str, user: str) -> dict:
        """准备文件数据根据传输方式"""
        logger.info(f"准备文件数据，源: {file_source}，方法: {method}")  # 文件数据准备日志
        if method == "local_file":
            if isinstance(file_source, bytes):
                error_msg = "local_file模式需要文件路径"
                logger.error(error_msg)  # 参数错误日志
                raise ValueError(error_msg)
            file_id = self.upload_file(file_source, user)
            return {
                "type": "image",
                "transfer_method": method,
                "upload_file_id": file_id
            }
        elif method == "remote_url":
            return {
                "type": "image",
                "transfer_method": method,
                "url": file_source
            }
        else:
            error_msg = f"不支持的传输方式: {method}"
            logger.error(error_msg)  # 不支持方法日志
            raise ValueError(error_msg)

    def _post_message(self, payload: dict) -> dict:
        """发送消息核心方法"""
        chat_url = f"{self.base_url}/chat-messages"  # 调整路径，移除重复的/v1
        # 请求详细日志（调试级别）
        logger.debug(
            f"发送POST请求到 {chat_url}，请求体: {json.dumps(payload, ensure_ascii=False)}")

        try:
            response = requests.post(
                chat_url,
                headers={**self.default_headers,
                         'Content-Type': 'application/json'},
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"消息发送成功，响应状态码: {response.status_code}")  # 成功响应日志
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")  # 请求异常日志
            raise RuntimeError(f"请求失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error("响应解析失败，非JSON格式响应")  # 解析失败日志
            raise RuntimeError("响应解析失败")


# 使用示例
if __name__ == "__main__":

    client = DifyClient(
        base_url="http://xuntian-ai-sit.tclpv.com/v1",  # 修改base_url为包含/v1的完整路径
        api_key="app-FpC7jmVhoS90BTUSfCxsm0gG"
    )

    try:
        result = client.send_message(
            query="分析图片",
            user="abc-123",
            file_source="https://xuntian-pv.tcl.com/group1/M00/1A/19/rBAAOGchjDeAZli9AAFfY8v0R18553.jpg",
            transfer_method="remote_url"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"远程请求错误: {str(e)}")
