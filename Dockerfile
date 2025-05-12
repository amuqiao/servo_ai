FROM python:3.12-slim-bookworm


# 替换系统源（根据基础镜像版本调整）
# RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list.d/debian.sources


# 导入Debian镜像的GPG密钥
RUN apt-get update && apt-get install -y gnupg2 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0E98404D386FA1D9 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 6ED0E7B82643E131 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F8D2585B8783D481

# 3. 导入 Debian 官方 GPG 密钥（清华源需使用官方密钥，密钥服务器用清华的）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    busybox-static \
    redis-tools \
    redis-server \
    supervisor \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录为 /app
# - 后续所有操作默认在此目录执行
# - 保持容器内路径与开发环境一致
WORKDIR /app

# 创建Redis数据目录并设置权限
RUN mkdir -p /var/lib/redis && \
    mkdir -p /var/log/redis && \
    chown -R root:root /var/lib/redis /var/log/redis

# 复制Redis配置文件
COPY redis.conf /etc/redis/redis.conf

# 复制Supervisor配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf 

# ====================== 替换 Python 源为清华源 ======================
# 复制依赖清单并安装（pip 源改为清华）
# 复制依赖清单
COPY requirements.txt /app/requirements.txt

# 创建虚拟环境并安装依赖
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt && \
    # 验证fastapi是否正确安装
    .venv/bin/fastapi --version

# 复制项目源码（确保.dockerignore排除不必要的文件）
COPY . /app

# 配置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app/src"

# 验证 uvicorn 安装
RUN uvicorn --version

# 重置入口点
ENTRYPOINT []

# 容器启动命令配置
# 使用 fastapi dev 命令：
# - 启用开发模式的热重载功能
# - 监听文件变化自动重启服务
# 设置 --host 0.0.0.0：
# - 允许从容器外部访问服务
# - 兼容 Docker 网络桥接模式
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
