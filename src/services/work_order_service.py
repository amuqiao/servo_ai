from src.schemas.work_order_schemas import WorkOrderRequest, OnTheWayWorkOrder
from src.exceptions.work_order_exceptions import WorkOrderException, WorkOrderErrorCode
import logging
import re
import ast
import time
from typing import Dict, List, Any
from src.configs.config import ApiConfig
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError  # 导入异步客户端
from aiocache import cached  # 导入异步缓存

logger = logging.getLogger(__name__)


class WorkOrderService:
    @staticmethod
    def extract_content_and_advice(work_order: WorkOrderRequest) -> Dict[str, Any]:
        """提取content和orderAdvice并组合成新的数据结构"""
        # 验证输入数据
        if not work_order.content:
            logger.error("工单内容content不能为空")
            raise WorkOrderException(
                code=WorkOrderErrorCode.WORK_ORDER_VALIDATE_FAILED,
                message="工单内容不能为空"
            )

        if not work_order.onTheWayWorkOrderList:
            logger.error("在途工单列表onTheWayWorkOrderList不能为空")
            raise WorkOrderException(
                code=WorkOrderErrorCode.WORK_ORDER_VALIDATE_FAILED,
                message="在途工单列表不能为空"
            )

        # 提取orderAdvice并保持原列表顺序
        order_advices = [item.orderAdvice for item in work_order.onTheWayWorkOrderList]

        # 组合新的数据结构
        combined_data = {
            "content": work_order.content,
            "orderAdvices": order_advices
        }

        logger.info(f"成功提取并组合工单数据，orderAdvices数量: {len(order_advices)}")
        return combined_data
    
    @staticmethod
    @cached(ttl=3600)
    async def calculate_similarity(content: str, order_advices: tuple) -> List[str]:
        """异步计算文本相似度"""
        if not content or not order_advices:
            raise ValueError("content和order_advices不能为空")

        prompt = f"""
<task>将工单内容与建议列表中的每条建议依次进行一对一语义相似度计算，严格按照输入顺序处理每个建议，为每条建议生成独立的连续相似度评分</task>

<context>
# Role：光伏行业工单语义相似度计算专家

## Background：
## Task：
将工单内容与建议列表中的每条建议依次进行一对一语义相似度计算，严格按照输入顺序处理每个建议，为每条建议生成独立的连续相似度评分。

## Background：
所有工单均为光伏电站运维领域文本，包含设备故障、安装问题、漏水维修等专业场景。

## Attention：
- 光伏行业术语必须优先识别和保留（如：光伏板、水槽、漏水、采光、安装高度、彩钢瓦等）
- 对于描述相同问题的不同表述必须判定为高度相似（如："光伏板漏雨"与"光伏板缝隙处漏水"应视为高度相似）
- 忽略文本长度差异，重点关注核心问题的语义一致性
- 严格控制输出格式，任何情况下不得添加解释性文字
- **领域相关性判断是重要因素**：必须首先判断每条建议是否属于光伏运维领域。对于完全不属于光伏运维领域的建议（如天气描述、无关行业内容），相似度评分应较低。
- **领域相关性判断标准**（严格执行）：必须包含至少一个**核心光伏术语**（光伏板/逆变器/支架/线缆/汇流箱/发电量/故障/维修/安装/清洁/漏水/短路/接地），且术语需在问题描述中承担关键语义角色
- **非光伏内容强制规则**：任何不含核心光伏术语的文本，相似度直接判定为**≤15%**，并在结果验证阶段进行二次确认
- **语义匹配优先级**：核心问题类型（故障/安装/清洁/维护等）> 涉及设备（光伏板/逆变器等）> 具体现象描述
- **相似度评分规则**：
  - 同一核心问题类型且涉及相同设备 → 85%-95%
  - 同一问题类型不同设备 → 60%-84%
  - 不同问题类型但相关领域 → 30%-59%
  - 非光伏领域内容 → ≤15%
  - 属于光伏领域但核心问题完全不同的内容 → 20%-30%
- 对于属于光伏领域但术语不完全匹配的内容，应根据其相关程度给出适当的相似度评分，而不是直接判定为不相关。
- **问题类型扩展**：明确维护类问题（如"请维护电站"）与故障类问题（如"设备故障"）的关联性，设定基础相似度≥40%
- **冲突案例处理**：当出现以下情况时进行人工规则干预：
  - 非光伏内容相似度>20% → 强制修正为15%
  - 明确包含核心光伏术语但相似度<30% → 基于术语匹配度提升至30-40%
  - 维护类与故障类问题匹配 → 基础相似度40%起评
- 结果合理性检查：
  - 非光伏内容（如天气、日常对话）必须≤15%（例："明天去哪儿玩"→10%）
  - 维护类与故障类问题必须≥40%（例："请维护电站"与"设备故障"→60%）
  - 同类问题（如不同表述的漏水问题）必须≥85%

## Profile：
- Author: pp
- Version: 0.2
- Language: 中文
- Description: 专注于光伏电站运维工单的语义相似度计算，能准确识别行业术语和同类问题的不同表述方式。

### Skills:
- 精通中文语义理解，尤其擅长技术领域文本分析
- 熟悉光伏电站运维专业术语和常见问题表述
- 能忽略表面文字差异，识别深层语义相似性
- 严格按照行业标准进行相似度评分

## Goals:
- 对工单内容进行深度语义分析而非字面匹配
- 识别光伏行业专业术语并作为相似度判断的重要依据
- 对描述相同运维问题的工单给予85%-95%的相似度评分
- 输出严格符合格式要求的JSON百分比列表

## Constrains:
- 必须使用基于BERT的语义相似度算法，不得使用Jaccard等字面匹配算法
- 对于包含相同核心问题（如漏水、安装问题、设备损坏）的工单，相似度必须≥85%
- 输出结果必须是严格的JSON数组格式，仅包含百分比字符串
- 必须保持输入列表的原始顺序

## Workflow:
1. **领域相关性判断**：检查每条建议是否包含至少一个光伏领域核心术语（光伏板、逆变器、支架、线缆、汇流箱、发电量、故障、维修、安装、清洁、漏水、短路、接地等）。
   - 完全不包含任何光伏领域专业术语的文本 → 相似度评分≤15%，继续后续步骤
   - 包含光伏领域专业术语的文本 → 继续执行后续步骤
2. **专业术语识别**：从`{content}`和`{list(order_advices)}`中提取光伏行业术语
3. **核心问题提取**：识别每个文本描述的核心运维问题
4. **语义相似度计算**：使用BERT算法计算核心问题的语义相似度
5. **结果校准**：根据相似度评分规则调整相似度分数
6. **结果验证**：双重检查确保非光伏领域内容相似度≤15%，光伏领域同类问题≥85%
7. **格式验证**：确保输出数组长度与输入orderAdvices列表长度完全一致
8. **格式输出**：生成JSON格式的百分比列表，不包含任何额外文字

## OutputFormat:
- 仅返回JSON数组，数组长度必须与输入的orderAdvices列表长度**严格一致**，多一个或少一个元素都视为格式错误
- 如果输入2个建议，输出必须是包含2个元素的数组，例如：["15%", "85%"]
- 每个元素为带百分号的字符串，保留整数
- 不得包含任何解释、说明或额外字符
- 结果合理性检查：确保所有非光伏领域内容相似度≤15%，光伏领域同类问题≥85%

## 光伏行业常见问题类型及示例：
1. **漏水问题**：
   - 光伏板漏雨 → 85%
   - 光伏板缝隙处漏水 → 90%
   - 水槽漏水 → 80%
   - 屋顶漏水 → 75%
   - 固定柱漏水 → 70%
2. **安装问题**：
   - 安装位置不当挡住采光 → 85%
   - 用户表示家里安装的光伏导致邻居说挡住他采光需要处理 → 80%
   - 农户邻居来电表示我们的光伏安装太高了，冬天挡住了自己的光线... → 85%
   - 安装高度过高 → 80%
   - 电表安装位置不合适 → 75%
3. **设备损坏**：
   - 光伏板损坏/裂开 → 85%
   - 光伏板掉落 → 80%
   - 彩钢瓦损坏 → 75%
4. **不相关内容示例**：
   - 天气描述（如："今天天气不错"、"明天会下雨"）→ 相似度评分≤15%
   - 完全不相关的行业内容（如："汽车发动机维修"、"手机APP开发"）→ 相似度评分≤15%
   - 光伏领域内容与非光伏领域内容的组合（如：工单内容为"设备故障"，建议为"今天天气不错"）→ 相似度评分≤15%
</context>

<instructions>
1. **领域相关性判断**：
   - 检查每条建议是否包含至少一个光伏领域核心术语（光伏板、逆变器、支架、线缆、汇流箱、发电量、故障、维修、安装、清洁、漏水、短路、接地等）
   - 完全不包含任何光伏领域专业术语的文本 → 相似度评分≤15%，继续后续步骤
   - 包含光伏领域专业术语的文本 → 继续执行后续步骤
2. **专业术语识别**：
   - 从`{content}`和`{list(order_advices)}`中提取光伏行业术语
3. **核心问题提取**：
   - 识别每个文本描述的核心运维问题
4. **语义相似度计算**：
   - 使用BERT算法计算核心问题的语义相似度
5. **结果校准**：
   - 根据相似度评分规则调整相似度分数
6. **结果验证**：
   - 双重检查确保非光伏领域内容相似度≤15%，光伏领域同类问题≥85%
7. **格式验证**：
   - 确保输出数组长度与输入orderAdvices列表长度完全一致
8. **格式输出**：
   - 生成JSON格式的百分比列表，不包含任何额外文字
</instructions>

<output_format>
- 仅返回JSON数组，数组长度必须与输入的orderAdvices列表长度**严格一致**，多一个或少一个元素都视为格式错误
- 如果输入2个建议，输出必须是包含2个元素的数组，例如：["15%", "85%"]
- 每个元素为带百分号的字符串，保留整数
- 不得包含任何解释、说明或额外字符
- 结果合理性检查：确保所有非光伏领域内容相似度≤15%，光伏领域同类问题≥85%
</output_format>
"""

        try:
            config = ApiConfig()
            api_key = config.dashscope.API_KEY
            if not api_key:
                raise WorkOrderException(
                    code=WorkOrderErrorCode.WORK_ORDER_SUBMIT_FAILED,
                    message="相似度计算服务未配置"
                )

            # 使用异步客户端
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=config.dashscope.BASE_URL,
            )

            start_time = time.time()
            try:
                
                
                # 异步调用API
                response = await client.chat.completions.create(
                    model="qwen-turbo",
                    messages=[
                        {"role": "system", "content": "你是严格的格式生成器，仅返回符合JSON格式的列表，不添加任何额外文字。"},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    temperature=0.0,
                    max_tokens=200,
                    timeout=30
                )
                logger.info(f"相似度计算成功，耗时{time.time() - start_time:.2f}秒")
            except APITimeoutError:
                raise WorkOrderException(
                    code=WorkOrderErrorCode.WORK_ORDER_SUBMIT_FAILED,
                    message="相似度计算超时，请稍后重试"
                )

            # 提取并净化结果
            logger.info(f"相似度计算原始结果: {response.choices[0].message.content.strip()}")
            result = response.choices[0].message.content.strip()
            list_match = re.search(r'\[.*?\]', result, re.DOTALL)
            if not list_match:
                raise WorkOrderException(
                    code=WorkOrderErrorCode.WORK_ORDER_FORMAT_ERROR,
                    message=f"无法提取列表格式: {result}"
                )
            clean_result = list_match.group()
            similarity_list = ast.literal_eval(clean_result)

            # 验证结果格式
            if not isinstance(similarity_list, list) or not all(isinstance(item, str) for item in similarity_list):
                raise WorkOrderException(
                    code=WorkOrderErrorCode.WORK_ORDER_FORMAT_ERROR,
                    message=f"结果格式错误: {similarity_list}"
                )

            return similarity_list

        except Exception as e:
            logger.error(f"相似度计算失败: {str(e)}")
            raise WorkOrderException(
                code=WorkOrderErrorCode.WORK_ORDER_CALCULATE_FAILED,
                message=f"相似度计算失败: {str(e)}"
            )

    @staticmethod
    def construct_response_data(work_order: WorkOrderRequest, similarity_rates: List[str]) -> Dict[str, Any]:
        """构造包含原始请求参数和相似度数据的响应结构"""
        # 转换相似度为小数并计算最大值
        similarity_values = []
        for rate in similarity_rates:
            try:
                # 移除百分号并转换为浮点数
                value = float(rate.replace('%', '')) / 100
                similarity_values.append(value)
            except (ValueError, TypeError):
                # 处理无效格式，默认为0
                similarity_values.append(0.0)
                logger.warning(f"无效的相似度格式: {rate}")

        # 计算最大相似度
        max_similarity = max(similarity_values) if similarity_values else 0.0

        # 复制原始工单列表并添加相似度
        on_the_way_list = []
        for order, rate in zip(work_order.onTheWayWorkOrderList, similarity_values):
            # 将Pydantic模型转换为字典（使用model_dump替代废弃的dict()方法）
            order_dict = order.model_dump()
            # 添加相似度作为repeatRate
            order_dict['repeatRate'] = rate
            on_the_way_list.append(order_dict)

        # 构造完整响应数据
        return {
            'repeatRate': max_similarity,
            'content': work_order.content,
            'onTheWayWorkOrderList': on_the_way_list
        }

    @staticmethod
    async def submit_work_order(work_order: WorkOrderRequest) -> Dict[str, Any]:
        """异步提交工单处理"""
        combined_data = WorkOrderService.extract_content_and_advice(work_order)
        # 异步调用相似度计算
        similarity_rates = await WorkOrderService.calculate_similarity(
            content=combined_data["content"],
            order_advices=tuple(combined_data["orderAdvices"])
        )

        response_data = WorkOrderService.construct_response_data(work_order, similarity_rates)
        return response_data

