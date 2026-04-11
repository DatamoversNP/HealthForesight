"""Shared configuration and settings"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration
    
    Configuration is loaded from environment variables with prefix DATABASE_
    or from .env file. The default value is only used if no environment variable is set.
    
    Environment variables:
    - DATABASE_URL: Full PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
    - DATABASE_POOL_SIZE: Connection pool size (default: 10)
    - DATABASE_MAX_OVERFLOW: Max overflow connections (default: 20)
    - DATABASE_ECHO: Enable SQL query logging (default: False)
    
    Example .env file:
        DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db
        DATABASE_POOL_SIZE=10
    """
    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="ignore")
    
    # Default value - only used if DATABASE_URL environment variable is not set
    # Override with DATABASE_URL environment variable or .env file
    # Common local setups:
    # - Local PostgreSQL: postgresql://postgres:postgres@localhost:5432/uepi_db
    # - Docker Compose: postgresql://uepi:uepi123@localhost:5432/uepi
    # - Homebrew PostgreSQL: postgresql://$(whoami)@localhost:5432/uepi_db
    url: str = "postgresql://postgres:postgres@localhost:5432/uepi_db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @field_validator("url", mode="before")
    @classmethod
    def strip_database_url(cls, v):
        """Avoid psycopg2 invalid sslmode when env has trailing/leading whitespace."""
        if isinstance(v, str):
            return v.strip()
        return v


class ObjectStorageSettings(BaseSettings):
    """Object storage (S3-compatible) configuration"""
    model_config = SettingsConfigDict(env_prefix="OBJECT_STORAGE_", extra="ignore")
    
    endpoint_url: str | None = None  # For MinIO/S3-compatible (defaults to endpoint if not set)
    endpoint: str = "http://localhost:9000"  # Legacy alias
    access_key_id: str | None = None  # For boto3 compatibility (defaults to access_key)
    access_key: str = "admin"  # Legacy alias
    secret_access_key: str | None = None  # For boto3 compatibility (defaults to secret_key)
    secret_key: str = "admin123"  # Legacy alias
    bucket_name: str = "uepi-data"  # For boto3 compatibility
    bucket: str = "uepi-data"  # Legacy alias
    region: str = "us-east-1"
    use_ssl: bool = False
    
    @property
    def endpoint_url_or_none(self) -> str | None:
        """Get endpoint URL, using endpoint_url if set, otherwise endpoint, or None for AWS"""
        return self.endpoint_url or (self.endpoint if self.endpoint != "http://localhost:9000" else None)
    
    @property
    def access_key_id_or_access_key(self) -> str:
        """Get access key ID, using access_key_id if set, otherwise access_key"""
        return self.access_key_id or self.access_key
    
    @property
    def secret_access_key_or_secret_key(self) -> str:
        """Get secret access key, using secret_access_key if set, otherwise secret_key"""
        return self.secret_access_key or self.secret_key
    
    @property
    def bucket_name_or_bucket(self) -> str:
        """Get bucket name, using bucket_name if set, otherwise bucket"""
        return self.bucket_name or self.bucket


class RedisSettings(BaseSettings):
    """Redis configuration"""
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")
    
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10


class OIDCSettings(BaseSettings):
    """OIDC authentication configuration"""
    model_config = SettingsConfigDict(env_prefix="OIDC_", extra="ignore")
    
    issuer: str = "http://localhost:8080/auth/realms/uepi"
    audience: str = "uepi-api"
    jwks_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None


class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    database: DatabaseSettings = DatabaseSettings()
    object_storage: ObjectStorageSettings = ObjectStorageSettings()
    redis: RedisSettings = RedisSettings()
    oidc: OIDCSettings = OIDCSettings()
    
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30

