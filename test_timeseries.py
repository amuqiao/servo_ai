#!/usr/bin/env python3
"""
时间序列预测功能测试脚本
"""

import requests
import json
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/predict/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_model_info():
    """测试获取模型信息"""
    print("\n=== 测试获取模型信息 ===")
    try:
        response = requests.get(f"{BASE_URL}/predict/model-info")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取模型信息失败: {e}")
        return False

def test_prediction():
    """测试预测功能"""
    print("\n=== 测试预测功能 ===")
    
    # 生成测试数据
    test_data = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    base_value = 100.0
    
    for i in range(24):
        timestamp = base_time + timedelta(hours=i)
        value = base_value + i + (i % 3) * 0.5  # 添加一些变化
        test_data.append({
            "timestamp": timestamp.isoformat(),
            "value": value
        })
    
    request_data = {
        "data": test_data,
        "forecast_horizon": 6,
        "context_length": 12
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"预测失败: {e}")
        return False

def test_test_endpoint():
    """测试测试端点"""
    print("\n=== 测试测试端点 ===")
    try:
        response = requests.post(f"{BASE_URL}/predict/test")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试端点失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始时间序列预测功能测试...")
    
    tests = [
        ("健康检查", test_health_check),
        ("模型信息", test_model_info),
        ("测试端点", test_test_endpoint),
        ("预测功能", test_prediction),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"执行测试: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "通过" if result else "失败"
            print(f"测试结果: {status}")
        except Exception as e:
            print(f"测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n{'='*50}")
    print("测试总结:")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")

if __name__ == "__main__":
    main() 