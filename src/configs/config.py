from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# 数据库配置类（添加 env_prefix 限制只读取 DB_ 前缀变量）
class DatabaseConfig(BaseSettings):
    """数据库模块配置（映射.env中DB_前缀的环境变量）"""
    host: str = Field("mysql")  # 自动映射 DB_HOST
    port: int = Field(3306)     # 自动映射 DB_PORT
    user: str = Field("root")   # 自动映射 DB_USER
    password: str = Field(...)  # 自动映射 DB_PASSWORD（无默认值，必须存在）
    db_name: str = Field(...)   # 自动映射 DB_NAME

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DB_",  # 新增：只读取 DB_ 前缀的环境变量
        extra="ignore",
    )

# Redis配置类（添加 env_prefix 限制只读取 REDIS_ 前缀变量）
class RedisConfig(BaseSettings):
    """Redis模块配置（映射.env中REDIS_前缀的环境变量）"""
    host: str = Field("localhost")  # 自动映射 REDIS_HOST
    port: int = Field(6379)         # 自动映射 REDIS_PORT
    password: str = Field(default="")  # 自动映射 REDIS_PASSWORD
    db: int = Field(default=0)       # 自动映射 REDIS_DB
    mode: str = Field(default='single')  # 自动映射 REDIS_MODE
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REDIS_",  # 新增：只读取 REDIS_ 前缀的环境变量
        extra="ignore",
    )

# Dify配置类（添加 env_prefix 限制只读取 DIFY_ 前缀变量）
class DifyConfig(BaseSettings):
    """Dify 模块配置（映射.env中DIFY_前缀的环境变量）"""
    BASE_URL: str = Field(...)  # 自动映射 DIFY_BASE_URL
    API_KEY: str = Field(...)   # 自动映射 DIFY_API_KEY
    TIMEOUT: int = Field(default=180)  # 自动映射 DIFY_TIMEOUT
    OCR_BASE_URL: str = Field(...)  # 自动映射 DIFY_OCR_BASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DIFY_",  # 只读取 DIFY_ 前缀的环境变量
        extra="ignore",
    )

class ApiConfig(BaseSettings):
    """项目全局配置类（整合各模块配置，从.env文件加载环境变量）"""
    ROOT_DIR: str = Field(default='./', env='ROOT_DIR')
    
    # 使用 default_factory 动态加载子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    dify: DifyConfig = Field(default_factory=DifyConfig)        

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # 保持允许全局额外变量（兼容历史配置）
    )
