# Use a Python image with uv pre-installed
FROM python:3.12-slim-bookworm

# 替换系统源（根据基础镜像版本调整）
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources
RUN pip install uv -i https://mirrors.aliyun.com/pypi/simple/


# Install the project into `/app/api`
WORKDIR /app/api

# 安装必要的工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # 工具
    busybox-static \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Application root directory
ENV ROOT_DIR=/app/api

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app/api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/api/.venv/bin:$PATH"

ENV PYTHONPATH="/app/api/src:/app/api:/app/api/src/api:$PYTHONPATH"
# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
# CMD ["fastapi", "dev", "--host", "0.0.0.0", "/app/api/src/api"]
# 根据MODE环境变量选择启动模式
CMD ["sh", "-c", "if [ \"$MODE\" = \"api\" ]; then exec fastapi dev --host 0.0.0.0 /app/api/src/api; elif [ \"$MODE\" = \"worker\" ]; then exec celery -A src.celery_app:app worker --loglevel=info; elif [ \"$MODE\" = \"beat\" ]; then exec celery -A src.celery_app:app beat --loglevel=info; else echo \"Unknown MODE: $MODE\"; exit 1; fi"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["fastapi", "dev", "--host", "0.0.0.0", "/app/api/main:app"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
