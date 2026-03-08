"""Factory for creating queue clients based on configuration"""
from typing import Optional

from uepi_common.queue.interface import QueueClient
from uepi_common.queue.redis import RedisQueueClient
from uepi_common.config import RedisSettings


def create_queue_client(
    settings: Optional[RedisSettings] = None,
    redis_url: Optional[str] = None,
    default_queue: str = "default",
) -> QueueClient:
    """Create appropriate queue client based on configuration
    
    Args:
        settings: RedisSettings instance (optional)
        redis_url: Override Redis URL
        default_queue: Default queue name
        
    Returns:
        QueueClient implementation (Redis for MVP)
        
    Examples:
        # Using settings
        client = create_queue_client(settings=RedisSettings())
        
        # Using direct URL
        client = create_queue_client(redis_url="redis://localhost:6379/0")
    """
    # For MVP, always use Redis
    # Future: Can add Azure Service Bus implementation here
    url = redis_url
    if not url and settings:
        url = settings.url
    
    if not url:
        url = "redis://localhost:6379/0"
    
    return RedisQueueClient(
        redis_url=url,
        default_queue=default_queue,
    )

