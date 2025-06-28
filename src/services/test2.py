import os
from openai import OpenAI


data = {
    "content": "工单内容示例",
    "orderAdvices": [
        "请检查设备运行状态"
        "请维护电站设备"
    ]}

prompt = """
帮我 判断下  data 中 content 和 orderAdvices 中每个元素的相似度

直接输出一个文本相似度 百分比 列表
示例：
rate:  [20%, 80%]

"""

try:
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY",
                          "sk-9ec27f85396f41788a441841e6d4a718"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "你是谁？"},
        ],
    )
    print(completion.choices[0].message.content)
except Exception as e:
    print(f"错误信息：{e}")
    print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
