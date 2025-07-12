import json
import os
from pathlib import Path
from typing import Dict, Callable
from src.exceptions.prompt_loader_exceptions import PromptLoaderException, PromptLoaderErrorCode

class PromptLoader:
    # 文件类型到加载方法的映射，便于未来扩展
    _LOADERS: Dict[str, Callable[[str], str]] = {
        'txt': '_load_txt_prompt',
        'json': '_load_json_prompt'
    }

    def __init__(self, root_dir: str = str(Path(__file__).parent.joinpath('prompts').resolve())):
        """
        初始化提示词加载器
        :param root_dir: 提示词根目录绝对路径
        """
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            raise PromptLoaderException(
                code=PromptLoaderErrorCode.PROMPT_FILE_NOT_FOUND,
                message=f"提示词根目录不存在: {self.root_dir}",
                details={"root_dir": str(self.root_dir)}
            )

    def load_prompt(self, prompt_path: str, file_type: str = 'txt') -> str:
        """
        加载提示词文件内容
        :param prompt_path: 提示词文件相对路径（相对于根目录），如"xxx.txt"或"xx/xx.txt"
        :param file_type: 文件类型，支持'txt'和'json'
        :return: 提示词内容字符串
        """
        # 解析并拼接完整路径
        full_path = self.root_dir.joinpath(prompt_path).resolve()

        # 检查文件是否存在
        if not full_path.exists():
            raise PromptLoaderException(
                code=PromptLoaderErrorCode.PROMPT_FILE_NOT_FOUND,
                message=f"提示词文件不存在: {full_path}",
                details={"file_path": str(full_path), "relative_path": prompt_path}
            )

        # 获取对应的加载方法
        loader_method = self._LOADERS.get(file_type.lower())
        if not loader_method:
            raise PromptLoaderException(
                code=PromptLoaderErrorCode.PROMPT_FILE_INVALID,
                message=f"不支持的提示词文件类型: {file_type}",
                details={"file_type": file_type, "supported_types": list(self._LOADERS.keys())}
            )

        # 调用对应的加载方法
        try:
            prompt = getattr(self, loader_method)(str(full_path))
        except Exception as e:
            raise PromptLoaderException(
                code=PromptLoaderErrorCode.PROMPT_LOAD_FAILED,
                message=f"加载{file_type}格式提示词失败: {str(e)}",
                details={"file_path": str(full_path), "error": str(e)}
            )

        # 检查提示词内容是否为空
        if not prompt.strip():
            raise PromptLoaderException(
                code=PromptLoaderErrorCode.PROMPT_EMPTY,
                message="提示词内容为空",
                details={"file_path": str(full_path)}
            )

        return prompt

    @staticmethod
    def _load_txt_prompt(prompt_path: str) -> str:
        """加载TXT格式的提示词"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _load_json_prompt(prompt_path: str) -> str:
        """加载JSON格式的提示词"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 尝试从JSON中获取提示词，支持多种可能的键名
        prompt = config.get('prompt', '').strip()
        if not prompt:
            prompt = config.get('content', '').strip()
        
        return prompt


if __name__ == "__main__":
    """测试提示词加载功能"""
    try:
        # 创建PromptLoader实例，使用默认根目录
        loader = PromptLoader()
        
        # 测试加载纳税人证明OCR提示词
        # prompt_path = "taxpayer_cert_ocr_prompt.txt"
        prompt_path = "test/test.txt"
        prompt_content = loader.load_prompt(prompt_path, file_type='txt')
        
        print(f"成功加载提示词文件: {prompt_path}")
        print("提示词内容:\n" + prompt_content)
    except PromptLoaderException as e:
        print(f"提示词加载失败: {e.message}")
        print(f"错误代码: {e.code}")
        print(f"详细信息: {e.details}")
    except Exception as e:
        print(f"发生未知错误: {str(e)}")