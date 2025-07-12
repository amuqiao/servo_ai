import pytest
from pathlib import Path
from src.tools.prompt_loader import PromptLoader
from src.exceptions.prompt_loader_exceptions import PromptLoaderException


def test_load_taxpayer_cert_prompt(tmp_path):
    # 创建临时提示词根目录
    root_dir = tmp_path / "prompts"
    root_dir.mkdir()
    print(f"创建临时提示词根目录: {root_dir}")
    
    # 创建普通提示词文件
    test_file = root_dir / "taxpayer_cert_ocr_prompt.txt"
    test_content = '请提取{"companyName": "测试公司", "taxpayerType": "小规模纳税人", "creditCode": "91500111MADAFDA278"}'
    test_file.write_text(test_content, encoding='utf-8')
    print(f"创建临时提示词文件: {test_file}, 内容: {test_content}")
    
    # 创建带目录的提示词文件
    subdir = root_dir / "subdir"
    subdir.mkdir()
    subdir_file = subdir / "nested_prompt.txt"
    subdir_content = '带目录的提示词内容'
    subdir_file.write_text(subdir_content, encoding='utf-8')
    print(f"创建临时目录提示词文件: {subdir_file}, 内容: {subdir_content}")
    
    # 初始化PromptLoader
    loader = PromptLoader(root_dir=str(root_dir))
    
    # 测试加载普通文件
    prompt = loader.load_prompt("taxpayer_cert_ocr_prompt.txt", file_type="txt")
    print("成功加载普通提示词内容:\n", prompt)
    assert prompt.strip() == test_content.strip(), "普通提示词内容不匹配"
    
    # 测试加载带目录的文件
    nested_prompt = loader.load_prompt("subdir/nested_prompt.txt", file_type="txt")
    print("成功加载带目录提示词内容:\n", nested_prompt)
    assert nested_prompt.strip() == subdir_content.strip(), "带目录提示词内容不匹配"
    
    # 验证关键内容
    expected_substrings = ['companyName', 'taxpayerType', 'creditCode', '小规模纳税人', '91500111MADAFDA278']
    for substring in expected_substrings:
        assert substring in prompt, f"提示词中缺少必要内容: {substring}"


def test_prompt_loader_exception_handling(tmp_path):
    # 创建临时提示词根目录
    root_dir = tmp_path / "prompts"
    root_dir.mkdir()
    loader = PromptLoader(root_dir=str(root_dir))
    
    # 创建测试文件
    test_file = root_dir / "test.txt"
    test_file.write_text("测试内容", encoding='utf-8')
    
    # 测试不存在的文件
    with pytest.raises(PromptLoaderException) as excinfo:
        loader.load_prompt("non_existent_file.txt")
    assert excinfo.value.code == 50030, "应该抛出文件不存在异常"
    
    # 测试不支持的文件类型
    with pytest.raises(PromptLoaderException) as excinfo:
        loader.load_prompt("test.txt", file_type="csv")
    assert excinfo.value.code == 50031, "应该抛出不支持的文件类型异常"
    
    # 测试空内容文件
    empty_file = root_dir / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    with pytest.raises(PromptLoaderException) as excinfo:
        loader.load_prompt("empty.txt")
    assert excinfo.value.code == 50032, "应该抛出提示词内容为空异常"