"""API configuration"""
from functools import lru_cache
from typing import Optional, Union
import json

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from uepi_common.config import (
    DatabaseSettings,
    OIDCSettings,
    ObjectStorageSettings,
    RedisSettings,
)


class APISettings(BaseSettings):
    """API-specific settings"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    # Union so env CORS_ORIGINS can be a plain string (e.g. "http://localhost:3000") without JSON
    cors_origins: Union[str, list[str]] = [
        "http://localhost:3050",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3050",
        "http://127.0.0.1:3000",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from env (string or JSON list) into list[str]."""
        if v is None:
            return None
        if isinstance(v, list):
            return v if v else None
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed if parsed else None
                if isinstance(parsed, str):
                    return [parsed] if parsed.strip() else None
                return None
            except (json.JSONDecodeError, ValueError, TypeError):
                origins = [origin.strip() for origin in v.split(",") if origin.strip()]
                return origins if origins else None
        return None
    
    database: DatabaseSettings = DatabaseSettings()
    object_storage: ObjectStorageSettings = ObjectStorageSettings()
    redis: RedisSettings = RedisSettings()
    oidc: OIDCSettings = OIDCSettings()
    
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # File-based storage (no database)
    use_file_storage: bool = True  # Use file storage instead of database
    storage_path: str = "./data"  # Base path for file storage
    
    # Azure File Storage (alternative to local file storage)
    use_azure_file_storage: bool = False  # Use Azure File Storage instead of local
    azure_storage_account_name: Optional[str] = None
    azure_storage_account_key: Optional[str] = None
    azure_storage_connection_string: Optional[str] = None  # Alternative to account_key
    azure_storage_file_share_name: str = "healthforesight-data"  # File share name
    
    # Conversational AI / LLM Settings
    llm_provider: str = "openai"  # "openai", "anthropic", or "local"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"  # or "gpt-4", "gpt-3.5-turbo"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"  # or "claude-3-sonnet-20240229"
    llm_temperature: float = 0.3  # Lower temperature for more deterministic outputs
    llm_max_tokens: int = 2000
    enable_rag: bool = True  # Enable Retrieval-Augmented Generation
    rag_top_k: int = 5  # Number of context chunks to retrieve
    enable_safety_guardrails: bool = True  # Enable content filtering and safety checks
    
    # Vector Search / Embeddings
    use_vector_search: bool = False  # Use embeddings instead of keyword matching
    embedding_provider: str = "openai"  # "openai" or "local"
    embedding_model: str = "text-embedding-3-small"  # OpenAI embedding model
    vector_store_path: str = "./data/vector_store"  # Path for vector store
    
    # Fine-tuning
    enable_fine_tuning: bool = False  # Enable fine-tuned models
    fine_tuned_model_id: Optional[str] = None  # Fine-tuned model ID
    
    # Caching
    enable_query_cache: bool = True  # Enable query result caching
    cache_ttl_seconds: int = 3600  # Cache TTL (1 hour)
    cache_backend: str = "memory"  # "memory", "redis", or "file"
    
    # Rate Limiting
    enable_rate_limiting: bool = True  # Enable rate limiting
    rate_limit_per_minute: int = 10  # Requests per minute per user
    rate_limit_per_hour: int = 100  # Requests per hour per user
    
    # Cost Tracking
    enable_cost_tracking: bool = True  # Track LLM API costs
    cost_tracking_path: str = "./data/cost_tracking"  # Path for cost logs

    # Async jobs: when False (default), elasticity runs via FastAPI BackgroundTasks after POST returns.
    # Set UEPI_USE_CELERY_FOR_ELASTICITY=true only if a Celery worker consumes the same Redis broker;
    # otherwise tasks sit in the queue and the UI polls until timeout.
    use_celery_for_elasticity: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "UEPI_USE_CELERY_FOR_ELASTICITY",
            "USE_CELERY_FOR_ELASTICITY",
        ),
    )

    # When False (default), daily pipeline runs via FastAPI BackgroundTasks. If True, enqueue
    # uepi_worker.tasks.daily_data_and_observations_job (requires a worker on the same Redis).
    use_celery_for_daily_job: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "UEPI_USE_CELERY_FOR_DAILY_JOB",
            "USE_CELERY_FOR_DAILY_JOB",
        ),
    )

    # When False (default), what-if POST /analyses/simulate runs via FastAPI BackgroundTasks on the API
    # process (no separate worker). If True, enqueue uepi_worker.tasks.whatif_scenario_job on Redis.
    use_celery_for_whatif_simulation: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "UEPI_USE_CELERY_FOR_WHATIF_SIMULATION",
            "USE_CELERY_FOR_WHATIF_SIMULATION",
        ),
    )


@lru_cache()
def get_settings() -> APISettings:
    """Get cached settings instance"""
    return APISettings()

