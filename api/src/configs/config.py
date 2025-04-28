from pydantic import BaseModel
from pydantic_settings import BaseSettings

class ApiConfig(BaseSettings):
    CELERY_BROKER_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        extra = "allow"