"""Worker configuration"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from uepi_common.config import (
    DatabaseSettings,
    ObjectStorageSettings,
    RedisSettings,
)


class WorkerSettings(BaseSettings):
    """Worker-specific settings"""
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables to avoid validation errors
    )
    
    environment: str = "development"
    log_level: str = "INFO"
    
    database: DatabaseSettings = DatabaseSettings()
    object_storage: ObjectStorageSettings = ObjectStorageSettings()
    redis: RedisSettings = RedisSettings()


@lru_cache()
def get_settings() -> WorkerSettings:
    """Get cached settings instance"""
    return WorkerSettings()

