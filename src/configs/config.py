from pydantic_settings import BaseSettings
from pydantic import Field

class ApiConfig(BaseSettings):
    
    DIFY_BASE_URL: str = Field(..., env="DIFY_BASE_URL")  # 例：http://xuntian-ai-sit.tclpv.com
    DIFY_API_KEY: str = Field(..., env="DIFY_API_KEY")   # 例：app-FpC7jmVhoS90BTUSfCxsm0gG
    DIFY_TIMEOUT: int = Field(default=180, env="DIFY_TIMEOUT")  # 超时时间，单位秒
    DIDY_OCR_BASE_URL: str = Field(..., env="DIDY_OCR_BASE_URL")
    ROOT_DIR: str = Field(default='./', env='ROOT_DIR')
    DB_HOST: str = Field(default='mysql', env='DB_HOST')
    DB_PORT: int = Field(default=3306, env='DB_PORT')
    DB_USER: str = Field(default='root', env='DB_USER')
    DB_PASSWORD: str = Field(env='DB_PASSWORD')
    DB_NAME: str = Field(env='DB_NAME')
    
    REDIS_HOST: str = Field(env='REDIS_HOST')
    REDIS_PORT: int = Field(env='REDIS_PORT')
    REDIS_PASSWORD: str = Field(default="", env='REDIS_PASSWORD')
    REDIS_DB: int = Field(default=0, env='REDIS_DB')
    REDIS_MODE: str = Field(default='single', env='REDIS_MODE')
    CELERY_BROKER_URL: str = Field(env='CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND: str = Field(env='CELERY_RESULT_BACKEND')
    # 扫描Redis任务的间隔时间（单位：秒）
    CELERY_SCAN_TASKS_INTERVAL: float = Field(default=10.0, env="CELERY_SCAN_TASKS_INTERVAL")  
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        extra = "allow"
