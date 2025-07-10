# Servo AI 项目文档

## 目录
- [项目简介](#项目简介)
- [环境要求](#环境要求)
- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

## 项目简介
Servo AI 是一个基于FastAPI和Celery的后端服务项目，提供光伏电站运维工单处理、OCR识别等功能。

## 环境要求
- Python 3.8+ 
- Redis 6.0+ 
- Docker (可选，用于容器化部署)

## 本地部署

### 1. 准备工作
```bash
# 克隆项目仓库后进入目录
cd servo_ai
```

### 2. 安装UV虚拟环境管理工具
根据操作系统选择以下一种方式安装：

```bash
# 方式1: 通过pip安装
pip install uv

# 方式2: Homebrew安装 (仅macOS)
brew install uv

# 方式3: 脚本安装 (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 方式4: PowerShell安装 (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 同步项目依赖
```bash
uv sync
```

### 4. 安装Redis
```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# Windows
choco install redis-64
```

### 5. 启动服务

#### 5.1 启动FastAPI应用
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### 5.2 启动Celery Beat (定时任务调度器)
```bash
celery -A src.celery_app:app beat
```

#### 5.3 启动Celery Worker (异步任务执行器)
```bash
celery -A src.celery_app.app worker --concurrency=4 --autoscale=8,4
```

#### 5.4 启动Flower (Celery监控工具)
```bash
celery -A src.celery_app:app flower --port=5555
```

### 6. 日志位置
本地日志文件存储在项目根目录的 `logs/` 文件夹下

## Docker部署

### 1. 构建镜像
```bash
# 指定版本号，默认为v1.0.x
docker build -t servo_ai_api:v1.0.x .
```

### 2. 启动容器
```bash
docker run -p 8000:8000 servo_ai_api:1.0.x supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
```

### 3. 查看容器日志
```bash
docker logs -f servo_ai_api
```

## API文档
服务启动后，可通过以下地址访问自动生成的API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 导出依赖
当更新了`pyproject.toml`中的依赖后，需要重新生成requirements.txt：
```bash
uv pip compile --output-file requirements.txt pyproject.toml
```

### 代码风格
- 遵循PEP 8规范
- 使用类型注解
- 编写单元测试

### 发版规则
```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程仓库
git push origin v1.0.0

# 查看已创建的标签
git tag
```

## 常见问题
- **Q: 服务启动后无法访问？**
  A: 检查端口是否被占用，尝试更换端口或关闭占用进程

- **Q: Redis连接失败？**
  A: 确认Redis服务已启动，检查配置文件中的Redis连接参数

- **Q: 依赖安装失败？**
  A: 尝试更新UV版本：`uv self-update`，或删除`uv.lock`后重新同步依赖