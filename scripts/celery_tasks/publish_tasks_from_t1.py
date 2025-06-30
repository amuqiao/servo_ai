import requests
import json
from t1 import data  # 导入t1.py中的业务ID列表
from typing import List
import time

# 配置
API_ENDPOINT = "http://121.37.12.192:8000/api/ocr/tasks/by-business-ids"
AI_STATUS = -1  # 查询参数ai_status的值
BATCH_SIZE = 100  # 每批发送的业务ID数量
RETRY_TIMES = 3  # 请求失败重试次数
RETRY_DELAY = 5  # 重试延迟时间(秒)
BATCH_DELAY = 20  # 批次间延迟时间(秒)
RESULT_FILE = "published_business_ids.txt"  # 已发布业务ID的结果文件路径

class TaskPublisher:
    @staticmethod
    def send_batch(batch: List[str]) -> dict:
        """发送一批业务ID到API端点

        参数:
            batch: 业务ID列表

        返回:
            dict: API响应结果
        """
        url = f"{API_ENDPOINT}?ai_status={AI_STATUS}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        for attempt in range(RETRY_TIMES):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(batch)
                )
                response.raise_for_status()  # 抛出HTTP错误
                return {
                    "success": True,
                    "data": response.json(),
                    "batch_size": len(batch)
                }
            except requests.exceptions.RequestException as e:
                if attempt < RETRY_TIMES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return {
                    "success": False,
                    "error": str(e),
                    "batch_size": len(batch),
                    "batch_sample": batch[:5]  # 只显示前5个ID作为参考
                }

    @staticmethod
    def publish_all_tasks():
        """发布t1.py中的所有业务ID任务"""
        total = len(data)
        success_count = 0
        failed_batches = []

        print(f"开始发布任务，共{total}个业务ID，每批{BATCH_SIZE}个")

        # 分批次处理
        for i in range(0, total, BATCH_SIZE):
            batch = data[i:i+BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            print(f"正在处理第{batch_num}批，共{len(batch)}个ID")

            result = TaskPublisher.send_batch(batch)
            if result["success"]:
                success_count += result["batch_size"]
                print(f"第{batch_num}批发布成功")
                # 将成功发布的业务ID写入结果文件
                try:
                    with open(RESULT_FILE, 'a', encoding='utf-8') as f:
                        for business_id in batch:
                            f.write(f"{business_id}\n")
                except IOError as e:
                    print(f"写入结果文件失败: {str(e)}")
            else:
                failed_batches.append({
                    "batch_num": batch_num,
                    "result": result
                })
                print(f"第{batch_num}批发布失败: {result['error']}")
            
            # 批次间延迟控制
            if BATCH_DELAY > 0 and (i + BATCH_SIZE) < total:
                print(f"等待{BATCH_DELAY}秒后处理下一批次...")
                time.sleep(BATCH_DELAY)

        # 输出汇总结果
        print("\n=== 发布结果汇总 ===")
        print(f"总任务数: {total}")
        print(f"成功发布: {success_count}")
        print(f"失败批次: {len(failed_batches)}")

        if failed_batches:
            print("失败批次详情:")
            for fb in failed_batches:
                print(f"批次 {fb['batch_num']}: {fb['result']['error']}")
                print(f"  样本ID: {fb['result']['batch_sample']}")

if __name__ == "__main__":
    TaskPublisher.publish_all_tasks()