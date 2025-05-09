import requests
import json
from typing import Optional, Union
from src.configs.config import ApiConfig
config = ApiConfig()

class DifyClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.timeout = timeout
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.default_headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'DifyClient/2.0',
            'Accept': 'application/json'
        }

    def upload_file(self, file_path: str, user: str) -> str:
        """上传本地文件并返回文件ID"""
        # 上传文件的URL
        upload_url = f"{self.base_url}/v1/files/upload"
        
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
                    headers={k:v for k,v in self.default_headers.items() if k != 'Content-Type'},
                    files=files,
                    data=data
                )
                
                if response.status_code == 201:
                    return response.json()['id']
                raise Exception(f"上传失败: {response.text}")
                
        except Exception as e:
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
        """
        发送带文件引用的聊天消息
        
        :param file_source: 文件路径（local_file模式）或图片URL（remote_url模式）
        :param transfer_method: 文件传输方式（local_file/remote_url）
        """
        # 处理文件资源
        file_data = self._prepare_file_data(file_source, transfer_method, user)
        
        # 构建请求体
        payload = {
            "inputs": {"file": file_data},
            "query": query,
            "response_mode": response_mode,
            "user": user,
            "files": [file_data]
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id

        return self._post_message(payload)

    def _prepare_file_data(self, file_source: Union[str, bytes], method: str, user: str) -> dict:
        """准备文件数据根据传输方式"""
        if method == "local_file":
            if isinstance(file_source, bytes):
                raise ValueError("local_file模式需要文件路径")
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
            raise ValueError(f"不支持的传输方式: {method}")

    def _post_message(self, payload: dict) -> dict:
        """发送消息核心方法"""
        chat_url = f"{self.base_url}/v1/chat-messages"
        
        try:
            response = requests.post(
                chat_url,
                headers={**self.default_headers, 'Content-Type': 'application/json'},
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError("响应解析失败")

# 使用示例
if __name__ == "__main__":
    client = DifyClient(
        base_url=config.DIFY_BASE_URL,
        api_key=config.DIFY_API_KEY
    )
    
    # 示例1：远程URL方式
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
    
