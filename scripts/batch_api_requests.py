import requests
import json

# 全局配置 - 可根据需要修改
API_URL = "http://139.9.51.165:8000/api/taxpayer-cert/recognize-cert"
URL_LIST = [
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/esigntest%E6%83%A0%E5%B7%9ETCL%E5%85%89%E4%BC%8F%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8PAAB.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E5%8F%A5%E5%AE%B9%E5%B8%82%E9%BC%8E%E5%A8%81%E6%96%B0%E8%83%BD%E6%BA%90%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E5%9B%9B%E5%B7%9D%E7%81%BF%E7%AB%8B%E8%83%BD%E6%BA%90%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E5%B1%B1%E4%B8%9C%E5%90%AF%E6%89%BF%E6%96%B0%E8%83%BD%E6%BA%90%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E5%B9%BF%E4%B8%9C%E6%99%96%E5%85%89%E6%96%B0%E8%83%BD%E6%BA%90%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E6%88%90%E9%83%BD%E5%B8%82%E5%96%84%E6%B0%B4%E5%96%84%E7%89%A9%E6%96%B0%E8%83%BD%E6%BA%90%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E6%9B%B2%E9%9D%96%E4%BA%91%E6%82%A6%E6%96%B0%E8%83%BD%E6%BA%90%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E6%AD%A6%E8%83%9C%E8%BD%A9%E5%AE%A5%E5%BB%BA%E7%AD%91%E5%8A%B3%E5%8A%A1%E6%9C%89%E9%99%90%E8%B4%A3%E4%BB%BB%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E6%B1%9F%E8%8B%8F%E6%99%9F%E9%91%AB%E6%96%B0%E8%83%BD%E6%BA%90%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.png",
    "https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/%E6%B1%9F%E8%A5%BF%E6%97%AD%E7%84%B6%E5%85%89%E4%BC%8F%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E8%B4%A3%E4%BB%BB%E5%85%AC%E5%8F%B8.png",
]


def send_batch_requests():
    """批量发送HTTP请求并打印格式化结果"""
    headers = {"Content-Type": "application/json"}
    total = len(URL_LIST)
    
    print(f"===== 开始批量请求 (共{total}个URL) =====\n")
    
    for index, url in enumerate(URL_LIST, start=1):
        payload = {"url": url}
        print(f"[{index}/{total}] 请求URL: {url}")
        print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            # 发送POST请求
            response = requests.post(
                API_URL,
                data=json.dumps(payload),
                headers=headers,
                timeout=30  # 设置30秒超时
            )
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            # 解析JSON响应
            result = response.json()
            print(f"响应状态: 成功 (HTTP {response.status_code})")
            print(f"响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            print(f"响应状态: 失败")
            print(f"错误信息: {str(e)}")
        except json.JSONDecodeError:
            print(f"响应状态: 失败")
            print(f"错误信息: 响应不是有效的JSON格式")
        
        print("-" * 50 + "\n")

if __name__ == "__main__":
    send_batch_requests()