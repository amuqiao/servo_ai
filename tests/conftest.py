from pathlib import Path
import sys

# 将项目根目录添加到 Python 搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

print(f"项目根目录: {project_root} 已添加到 Python 搜索路径")