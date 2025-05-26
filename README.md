# 本地启动服务
## 配置本地环境
```
cd servo_ai_api
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
celery -A src.celery_app:app worker
```
## 本地日志输出路径
```
logs/
```


