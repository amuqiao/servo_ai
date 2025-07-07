import ast
import sys
import json

# 正确执行命令示例:
# 1. 切换到脚本目录: cd /Users/wangqiao/Downloads/github_project/servo_ai_project/servo_ai/servo_ai/scripts/celery_tasks/0702
# 2. 执行脚本: python extract_company_ids.py " t1.py"
# 或使用绝对路径执行: python /Users/wangqiao/Downloads/github_project/servo_ai_project/servo_ai/servo_ai/scripts/celery_tasks/0702/extract_company_ids.py /Users/wangqiao/Downloads/github_project/servo_ai_project/servo_ai/servo_ai/scripts/celery_tasks/0702/t1.py


def extract_company_ids(file_path):
    """从指定的t1.py文件中提取company_id列表"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析Python文件，安全提取data变量
        tree = ast.parse(content)
        data = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id == 'data':
                    data = ast.literal_eval(node.value)
                    break

        if not data:
            raise ValueError("文件中未找到data变量")

        # 提取公司ID列表并转换为字符串
        company_ids = []
        for item in data.get('data', {}).get('data', []):
            company_id = item.get('company_id')
            if company_id is not None:
                company_ids.append(str(company_id))

        return company_ids

    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {file_path}")
    except Exception as e:
        raise RuntimeError(f"提取公司信息失败: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python extract_company_ids.py <t1.py文件路径>")
        sys.exit(1)

    t1_file_path = sys.argv[1]
    try:
        company_ids = extract_company_ids(t1_file_path)

        print(f"成功提取到{len(company_ids)}个公司ID:")
        print(json.dumps(company_ids))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
