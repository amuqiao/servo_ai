import os
import re
import ast
from openai import OpenAI
from typing import Dict, List


def calculate_similarity(data: Dict[str, any]) -> List[str]:
    """
    计算content与orderAdvices中每个元素的文本相似度
    :param data: 包含content和orderAdvices的字典
    :return: 相似度百分比列表（如["20%", "80%"]）
    """
    # 验证输入数据完整性
    if not all(key in data for key in ['content', 'orderAdvices']):
        raise ValueError("输入数据必须包含'content'和'orderAdvices'字段")
    if not data['orderAdvices']:
        return []

    # 构建严格格式化的提示词
    prompt = f"""
    任务：计算文本相似度并返回百分比列表
    1. 比较内容："{data['content']}"
    2. 比较对象列表：{data['orderAdvices']}
    3. 输出要求：
       - 仅返回JSON格式的百分比列表，不包含任何解释文字
       - 示例输出：[0.85, 0.60, 0.30]
       - 确保列表元素用双引号包裹，逗号分隔
    """

    try:
        # 初始化大模型客户端（使用兼容OpenAI格式的DashScope接口）
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY", "sk-9ec27f85396f41788a441841e6d4a718"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        # 调用大模型（更换为更稳定的qwen-turbo模型）
        response = client.chat.completions.create(
            model="qwen-turbo",  # 已验证可用的模型名称
            messages=[
                {"role": "system", "content": "你是严格的格式生成器，仅返回符合JSON格式的列表，不添加任何额外文字。"},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.0,  # 确定性模式，确保格式稳定
            max_tokens=200
        )

        # 提取并净化结果（关键修复）
        result = response.choices[0].message.content.strip()
        
        # 1. 使用正则提取最外层列表结构
        list_match = re.search(r'\[.*?\]', result, re.DOTALL)
        if not list_match:
            raise ValueError(f"无法提取列表格式: {result}")
        clean_result = list_match.group()
        
        # 2. 使用ast.literal_eval安全解析（替代eval，避免安全风险）
        similarity_list = ast.literal_eval(clean_result)
        
        # 3. 验证结果格式
        if not isinstance(similarity_list, list) or not all(isinstance(item, str) for item in similarity_list):
            raise ValueError(f"结果格式错误: {similarity_list}")

        return similarity_list

    except Exception as e:
        print(f"相似度计算失败: {str(e)}")
        raise


# 示例调用
if __name__ == "__main__":
    # 测试数据
    test_data = {
        "content": "设备故障",
        "orderAdvices": [
            "请检查设备运行状态",
            "请维护电站设备",
            "设备需要更换零件"
        ]
    }

    # 计算相似度
    try:
        similarity_rates = calculate_similarity(test_data)
        print(f"rate: {similarity_rates}")
    except Exception as e:
        print(f"执行失败: {e}")
