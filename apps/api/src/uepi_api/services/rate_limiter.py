"""Rate limiting for Conversational AI"""
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
from collections import defaultdict
import time

from uepi_api.config import get_settings

settings = get_settings()


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self):
        self.enabled = settings.enable_rate_limiting
        self.per_minute = settings.rate_limit_per_minute
        self.per_hour = settings.rate_limit_per_hour
        
        # In-memory tracking (in production, use Redis)
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
    
    def _get_user_key(self, user_id: UUID) -> str:
        """Get cache key for user"""
        return str(user_id)
    
    def _cleanup_old_requests(self, user_key: str):
        """Remove expired request timestamps"""
        now = datetime.now(timezone.utc)
        
        # Clean minute requests (older than 1 minute)
        self.minute_requests[user_key] = [
            ts for ts in self.minute_requests[user_key]
            if (now - ts).total_seconds() < 60
        ]
        
        # Clean hour requests (older than 1 hour)
        self.hour_requests[user_key] = [
            ts for ts in self.hour_requests[user_key]
            if (now - ts).total_seconds() < 3600
        ]
    
    def check_rate_limit(self, user_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit
        
        Returns:
            (allowed, error_message)
        """
        if not self.enabled:
            return True, None
        
        user_key = self._get_user_key(user_id)
        now = datetime.now(timezone.utc)
        
        # Cleanup old requests
        self._cleanup_old_requests(user_key)
        
        # Check minute limit
        minute_count = len(self.minute_requests[user_key])
        if minute_count >= self.per_minute:
            return False, f"Rate limit exceeded: {self.per_minute} requests per minute"
        
        # Check hour limit
        hour_count = len(self.hour_requests[user_key])
        if hour_count >= self.per_hour:
            return False, f"Rate limit exceeded: {self.per_hour} requests per hour"
        
        # Record request
        self.minute_requests[user_key].append(now)
        self.hour_requests[user_key].append(now)
        
        return True, None
    
    def get_remaining_requests(self, user_id: UUID) -> Dict[str, int]:
        """Get remaining requests for user"""
        if not self.enabled:
            return {"minute": self.per_minute, "hour": self.per_hour}
        
        user_key = self._get_user_key(user_id)
        self._cleanup_old_requests(user_key)
        
        return {
            "minute": max(0, self.per_minute - len(self.minute_requests[user_key])),
            "hour": max(0, self.per_hour - len(self.hour_requests[user_key]))
        }

