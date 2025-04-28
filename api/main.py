from fastapi import FastAPI
from routers import health_check, task_router
from celery_app import app as celery_app

# app = FastAPI()
app = FastAPI(title="ServoAI_API", version="1.0.0")

# 注册路由模块
# app.include_router(health_check.router)
# app.include_router(task_router.router)


# 路由注册
app.include_router(health_check.router, prefix="/api")
app.include_router(task_router.router, prefix="/api/tasks")

# 初始化Celery应用
@app.on_event('startup')
async def startup_event():
    celery_app.conf.update(app.config)
    
# Celery集成
@app.on_event("startup")
async def initialize_celery():
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json"
    )
    
@app.get("/")
async def root():
    return "Hello world2"

if __name__ == "__main__":
    pass
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # import uvicorn
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)