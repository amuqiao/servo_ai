import requests
import json
from typing import List
import time

# 配置
API_BASE_URL = "http://localhost:8000"
# 修正端点URL以匹配curl命令中的实际接口路径
PUBLISH_ENDPOINT = f"{API_BASE_URL}/demo-tasks/queue/single"


class TaskPublisher:
    @staticmethod
    def publish_single_task(urls: List[str]) -> dict:
        """构造并发送单个OCR任务请求

        参数:
            urls: 需要处理的URL列表

        返回:
            dict: 包含任务ID和状态的响应
        """
        # 构造符合DemoTaskRequest格式的请求数据
        task_data = {
            "task_data": {
                "content": {
                    "urls": urls
                },
                "task_id": f"1844_GF230815102545000535",
                "task_type": "ocr_cert_processing"
            }
        }

        try:
            response = requests.post(
                PUBLISH_ENDPOINT,
                json=task_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {str(e)}")
            raise


if __name__ == "__main__":
    # 示例URL列表
    test_urls = [
        "https://xuntian-pv.tcl.com/group1/M00/1A/19/rBAAOGchjDeAZli9AAFfY8v0R18553.jpg",
        "https://xuntian-pv.tcl.com/group1/M00/1A/19/rBAAOGchjDeAZli9AAFfY8v0R18553.jpg"  # 替换为实际URL
    ]
    test_urls = [
        "https://xuntian-pv.tcl.com/group1/M00/5E/1B/rBAAOGg4P6SABizqAAXiFV_wwKU981.pdf",
    ]

    test_urls = ["https://xuntian-pv.tcl.com/group1/M00/5E/1B/rBAAOGg4P6SABizqAAXiFV_wwKU981.pdf",
                 "https://xuntian-pv.tcl.com/group1/M00/5F/E1/rBAAOGg4dASAS27wAAQSa2bb0lQ943.jpg",
                 "https://xuntian-pv.tcl.com/group1/M00/5F/E1/rBAAOGg4dASAX4Y0AAYdsUBu234125.pdf",
                 "https://xuntian-pv.tcl.com/group1/M00/5F/F0/rBAAOGg4dc-AakrSAAYdsUBu234394.pdf",
                 "https://xuntian-pv.tcl.com/group1/M00/5F/F1/rBAAOGg4dc-ATdxHAAQSa2bb0lQ809.jpg",
                 "https://xuntian-pv.tcl.com/group1/M00/58/5A/rBAAOGg3iVSAOzGhAAXho7zlaUw240.pdf",
                 ]
    try:
        result = TaskPublisher.publish_single_task(test_urls)
        print(f"任务发布成功: {result}")
    except Exception as e:
        print(f"任务发布失败: {str(e)}")
