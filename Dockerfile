# Use a Python image with uv pre-installed
FROM python:3.12-slim-bookworm

# 替换系统源（根据基础镜像版本调整）
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources
# http://mirrors.aliyun.com/pypi/simple/
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 安装uv
RUN pip install uv -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Install the project into `/app/api`
WORKDIR /app/api

# 安装必要的工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # 工具
    busybox-static \
    redis-tools \
    redis-server \
    # 管理celery进程
    supervisor \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制Redis配置文件
COPY redis.conf /etc/redis/redis.conf

# Application root directory
ENV ROOT_DIR=/app/api

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
# # 在uv同步阶段增加超时和重试参数
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --index-url http://mirrors.aliyun.com/pypi/simple/
# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app/api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --index-url http://mirrors.aliyun.com/pypi/simple/

# Place executables in the environment at the front of the path
ENV PATH="/app/api/.venv/bin:$PATH"

ENV PYTHONPATH="/app/api/src:/app/api:/app/api/src/api"
# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
# CMD ["fastapi", "dev", "--host", "0.0.0.0", "src/api"]
CMD ["supervisord", "-n", "-c", "/app/api/supervisord.conf"]
# 根据MODE环境变量选择启动模式
# CMD ["sh", "-c", "if [ \"$MODE\" = \"api\" ]; then exec fastapi dev --host 0.0.0.0 /app/api/src/api; elif [ \"$MODE\" = \"worker\" ]; then exec celery -A src.celery_app:app worker --loglevel=info; elif [ \"$MODE\" = \"beat\" ]; then exec celery -A src.celery_app:app beat --loglevel=info; else echo \"Unknown MODE: $MODE\"; exit 1; fi"]

