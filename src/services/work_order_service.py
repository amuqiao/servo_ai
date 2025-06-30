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
    @cached(ttl=3600)  # 异步缓存替代lru_cache
    async def calculate_similarity(content: str, order_advices: tuple) -> List[str]:
        """异步计算文本相似度"""
        if not content or not order_advices:
            raise ValueError("content和order_advices不能为空")

        prompt = f"""
        任务：计算文本相似度并返回百分比列表
        1. 比较内容："{content}"
        2. 比较对象列表：{list(order_advices)}
        3. 输出要求：
           - 仅返回JSON格式的百分比列表，不包含任何解释文字
           - 示例输出：["85%", "60%", "30%"]
           - 确保列表元素用双引号包裹，逗号分隔
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

