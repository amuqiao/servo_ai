import requests
import json
from t2_work_orders import data

# 全局变量引用工单数据
global WORK_ORDERS_DATA
WORK_ORDERS_DATA = data

API_URL = "http://localhost:8000/api/work-order/submit"

def submit_work_orders():
    """提交工单列表到API接口"""
    for group in WORK_ORDERS_DATA:
        if len(group) < 2:
            print(f"跳过无效工单组（需要2个工单）: {group}")
            continue

        # 提取工单内容
        content = group[0]
        order_advice_1 = group[0]
        order_advice_2 = group[1]

        # 构造请求参数
        payload = {
            "repeatRate": 0.5,
            "content": content,
            "onTheWayWorkOrderList": [
                {
                    "id": "",
                    "orderAdvice": order_advice_1,
                    "powerName": "",
                    "powerNumber": "",
                    "startTime": "",
                    "taskId": "",
                    "taskStatus": 0
                },
                {
                    "id": "",
                    "orderAdvice": order_advice_2,
                    "powerName": "",
                    "powerNumber": "",
                    "startTime": "",
                    "taskId": "",
                    "taskStatus": 0
                }
            ]
        }

        # 发送POST请求
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                API_URL,
                data=json.dumps(payload),
                headers=headers
            )
            response.raise_for_status()  # 抛出HTTP错误
            response_data = response.json()
            data = response_data.get('data', {})
            main_repeat = data.get('repeatRate', 0)  # 最外层repeatRate作为max
            order_repeats = [item.get('repeatRate', 0) for item in data.get('onTheWayWorkOrderList', [])]
            all_repeats = order_repeats  # 仅保留工单列表中的repeatRate
            max_repeat = main_repeat  # 直接使用最外层值作为最大值
            print(f"工单组提交成功: {response_data}")
            print(f"repeatRate列表: {all_repeats}, 最大repeatRate: {max_repeat}")
        except requests.exceptions.RequestException as e:
            print(f"工单组提交失败: {str(e)}")
            print(f"请求参数: {payload}")

if __name__ == "__main__":
    submit_work_orders()