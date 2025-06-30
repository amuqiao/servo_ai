# 导入标准库：用于高精度时间测量（比 time.time() 更适合性能分析）
import time

# 导入 functools 模块的 wraps 装饰器：用于保留被装饰函数的元信息（如 __name__、__doc__）
from functools import wraps


def measure(func):
    """
    装饰器：用于测量函数的执行时间并打印结果

    参数:
        func (callable): 被装饰的目标函数

    返回:
        callable: 包装后的函数（保留原函数元信息）
    """

    @wraps(func)  # 保留被装饰函数的元信息（如函数名、文档字符串）
    def wrapper(*args, **kwargs):
        # 记录函数执行的起始时间（使用 perf_counter 保证高精度）
        start_time = time.perf_counter()
        # 执行原函数并获取返回值（传递所有位置参数和关键字参数）
        result = func(*args, **kwargs)
        # 记录函数执行的结束时间
        end_time = time.perf_counter()
        # 打印执行时间（格式化为保留4位小数的秒数）
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f} 秒")
        return result  # 返回原函数的执行结果

    return wrapper
