# 本地启动服务
## 配置本地环境
```
cd servo_ai
# 同步依赖
uv sync

```
## 启动服务

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 启动beat
```
celery -A src.celery_app:app beat
```
## 启动worker
```
celery -A src.celery_app.app worker --concurrency=4 --autoscale=8,4
```

## 启动flower
```
celery -A src.celery_app:app flower --port=5555
```

## 本地日志输出路径
```
logs/
```

# docker启动服务
## 构建镜像
```bash
# 指定版本号，默认为v1.0.x
docker build -t servo_ai_api:v1.0.x .

## 启动容器
docker run -p 8000:8000 servo_ai_api:1.0.x supervisord -n -c /etc/supervisor/conf.d/supervisord.conf 


## 查看容器日志
docker logs -f servo_ai_api
```


## 导出依赖
```
uv pip compile --output-file requirements.txt pyproject.toml
```

