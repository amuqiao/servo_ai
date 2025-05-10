from pydantic_settings import BaseSettings
from pydantic import Field

class ApiConfig(BaseSettings):
   
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="./logs", env="LOG_DIR")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_DATE_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S", env="LOG_DATE_FORMAT")
    LOG_FILE_MAX_SIZE: int = Field(default=10, env="LOG_FILE_MAX_SIZE")
    LOG_FILE_BACKUP_COUNT: int = Field(default=3, env="LOG_FILE_BACKUP_COUNT")
    LOG_TIMEZONE: str = Field(default="Asia/Shanghai", env="LOG_TIMEZONE")
    
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

    class Config:
        env_file = ".env"  # 显式指定.env文件路径
        env_file_encoding = "utf-8"  # 文件编码格式
        env_prefix = ""  # 环境变量前缀
        extra = "allow"