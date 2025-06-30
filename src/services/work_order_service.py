from src.schemas.work_order_schemas import WorkOrderRequest, OnTheWayWorkOrder
from src.exceptions.work_order_exceptions import WorkOrderException, WorkOrderErrorCode
import logging
import re
import ast
import time
from functools import lru_cache
from openai import OpenAI, Timeout
from typing import Dict, List, Any
from src.configs.config import ApiConfig

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

        logger.info(f"成功提取并组合工单数据，content: {work_order.content[:50]}, orderAdvices数量: {len(order_advices)}")
        return combined_data

    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_similarity(content: str, order_advices: tuple) -> List[str]:
        """
        计算content与orderAdvices中每个元素的文本相似度
        :param content: 工单内容文本
        :param order_advices: 建议文本元组（需可哈希）
        :return: 相似度百分比列表（如["20%", "80%"]）
        """
        # 验证输入数据完整性
        if not content or not order_advices:
            raise ValueError("content和order_advices不能为空")

        # 构建严格格式化的提示词
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
            # 初始化大模型客户端（使用兼容OpenAI格式的DashScope接口）
            config = ApiConfig()
            api_key=config.dashscope.API_KEY
            if not api_key:
                logger.error("未配置DASHSCOPE_API_KEY环境变量")
                raise WorkOrderException(
                    code=WorkOrderErrorCode.WORK_ORDER_SUBMIT_FAILED,
                    message="相似度计算服务未配置"
                )

            client = OpenAI(
                api_key=api_key,
                base_url=config.dashscope.BASE_URL,
            )

            # 调用大模型（使用qwen-turbo模型，添加超时控制）
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model="qwen-turbo",
                    messages=[
                        {"role": "system", "content": "你是严格的格式生成器，仅返回符合JSON格式的列表，不添加任何额外文字。"},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    temperature=0.0,
                    max_tokens=200,
                    timeout=20  # 10秒超时
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
    def submit_work_order(work_order: WorkOrderRequest) -> Dict[str, Any]:
        """提交工单并返回处理后的数据"""
        # 提取并组合数据
        combined_data = WorkOrderService.extract_content_and_advice(work_order)

        # 计算相似度（将列表转换为元组以支持缓存）
        similarity_rates = WorkOrderService.calculate_similarity(
            content=combined_data["content"],
            order_advices=tuple(combined_data["orderAdvices"])
        )

        # 构造响应数据
        response_data = WorkOrderService.construct_response_data(work_order, similarity_rates)
        logger.info(f"工单相似度计算完成，共{len(similarity_rates)}个建议项")
        return response_data

