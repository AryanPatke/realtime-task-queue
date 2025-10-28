from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    workers: int = 4
    
    # Task Settings
    max_retries: int = 3
    task_timeout: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

