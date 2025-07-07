from src.schemas.work_order_schemas import WorkOrderRequest, OnTheWayWorkOrder
from src.exceptions.work_order_exceptions import WorkOrderException, WorkOrderErrorCode
import logging
import re
import ast
import time
from typing import Dict, List, Any
from src.configs.config import ApiConfig
from openai import AsyncOpenAI, Timeout  # 导入异步客户端
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
    async def calculate_similarity(content: str, order_advices: tuple) -> List[str]:
        """异步计算文本相似度"""
        if not content or not order_advices:
            raise ValueError("content和order_advices不能为空")

        prompt = f"""
# Role：光伏行业工单语义相似度计算专家

## Background：
用户需要对光伏电站运维工单内容进行高精度语义相似度计算，特别是针对相似派单场景需要达到90%左右的相似度评分。所有工单均为光伏电站运维领域文本，包含设备故障、安装问题、漏水维修等专业场景。

## Attention：
- 光伏行业术语必须优先识别和保留（如：光伏板、水槽、漏水、采光、安装高度、彩钢瓦等）
- 对于描述相同问题的不同表述必须判定为高度相似（如："光伏板漏雨"与"光伏板缝隙处漏水"应视为高度相似）
- 忽略文本长度差异，重点关注核心问题的语义一致性
- 严格控制输出格式，任何情况下不得添加解释性文字

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
1. **专业术语识别**：从`{content}`和`{list(order_advices)}`中提取光伏行业术语（光伏板、漏水、水槽、采光等）
2. **核心问题提取**：识别每个文本描述的核心运维问题（如：光伏板漏水、安装位置不当、设备损坏等）
3. **语义相似度计算**：使用BERT算法计算核心问题的语义相似度，重点关注：
   - 问题类型一致性（如都是漏水问题）
   - 涉及设备一致性（如都是光伏板问题）
   - 故障现象相似性
4. **结果校准**：对相似问题的评分进行校准，确保同类问题相似度≥85%
5. **格式输出**：生成JSON格式的百分比列表，不包含任何额外文字

## OutputFormat:
- 仅返回JSON数组，如：["92%", "88%", "35%"]
- 列表长度必须与比较对象列表完全一致
- 每个元素为带百分号的字符串，保留整数
- 不得包含任何解释、说明或额外字符

## 光伏行业常见问题类型及示例：
1. **漏水问题**：
   - 光伏板漏雨
   - 光伏板缝隙处漏水
   - 水槽漏水
   - 屋顶漏水
   - 固定柱漏水
2. **安装问题**：
   - 安装位置不当挡住采光
   - 安装高度过高
   - 电表安装位置不合适
3. **设备损坏**：
   - 光伏板损坏/裂开
   - 光伏板掉落
   - 彩钢瓦损坏

## Initialization
作为光伏行业工单语义相似度计算专家，你现在开始处理光伏电站运维工单的相似度计算任务，重点关注语义一致性而非字面匹配，确保同类问题获得≥85%的相似度评分。
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
                    timeout=20
                )
                logger.info(f"相似度计算成功，耗时{time.time() - start_time:.2f}秒")
            except Timeout:
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

