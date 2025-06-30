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
    BASE_URL: str = Field(...)
    API_KEY: str = Field(...)
    TIMEOUT: int = Field(default=180)
    OCR_BASE_URL: str = Field(...)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DIFY_",
        extra="ignore",
    )

# DashScope配置类
class DashScopeConfig(BaseSettings):
    """DashScope 模块配置"""
    BASE_URL: str = Field(...)
    API_KEY: str = Field(...)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DASHSCOPE_",
        extra="ignore",
    )

class ApiConfig(BaseSettings):
    """项目全局配置类"""
    ROOT_DIR: str = Field(default='./', env='ROOT_DIR')
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    dify: DifyConfig = Field(default_factory=DifyConfig)
    dashscope: DashScopeConfig = Field(default_factory=DashScopeConfig) 

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # 保持允许全局额外变量（兼容历史配置）
    )
