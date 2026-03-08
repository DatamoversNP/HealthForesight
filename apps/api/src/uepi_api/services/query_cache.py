"""Query caching system for Conversational AI"""
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uepi_api.config import get_settings
from uepi_api.storage_file import BASE_PATH

settings = get_settings()


class QueryCache:
    """Cache for query results"""
    
    def __init__(self):
        self.cache_backend = settings.cache_backend.lower()
        self.ttl_seconds = settings.cache_ttl_seconds
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if self.cache_backend == "file":
            self.cache_dir = BASE_PATH / "query_cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        elif self.cache_backend == "redis":
            # Redis would be initialized here
            self.redis_client = None
            try:
                import redis
                from uepi_api.config import get_settings
                s = get_settings()
                if s.redis.host:
                    self.redis_client = redis.Redis(
                        host=s.redis.host,
                        port=s.redis.port or 6379,
                        db=0,
                        decode_responses=True
                    )
            except ImportError:
                print("Redis not available, falling back to memory cache")
                self.cache_backend = "memory"
    
    def _generate_cache_key(self, query: str, mode: str, domain: Optional[str], user_roles: tuple) -> str:
        """Generate cache key from query parameters"""
        key_data = {
            "query": query.lower().strip(),
            "mode": mode,
            "domain": domain,
            "roles": sorted(user_roles)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, query: str, mode: str, domain: Optional[str], user_roles: tuple) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        cache_key = self._generate_cache_key(query, mode, domain, user_roles)
        
        if self.cache_backend == "memory":
            if cache_key in self.memory_cache:
                cached = self.memory_cache[cache_key]
                expires_at = cached.get("expires_at")
                if expires_at and datetime.now(timezone.utc) < datetime.fromisoformat(expires_at):
                    return cached.get("data")
                else:
                    # Expired, remove
                    del self.memory_cache[cache_key]
            return None
        
        elif self.cache_backend == "file":
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cached = json.load(f)
                    expires_at = cached.get("expires_at")
                    if expires_at and datetime.now(timezone.utc) < datetime.fromisoformat(expires_at):
                        return cached.get("data")
                    else:
                        # Expired, remove
                        cache_file.unlink()
                except Exception:
                    pass
            return None
        
        elif self.cache_backend == "redis" and self.redis_client:
            try:
                cached = self.redis_client.get(f"query_cache:{cache_key}")
                if cached:
                    data = json.loads(cached)
                    return data.get("data")
            except Exception:
                pass
            return None
        
        return None
    
    def set(self, query: str, mode: str, domain: Optional[str], user_roles: tuple, data: Dict[str, Any]):
        """Cache result"""
        cache_key = self._generate_cache_key(query, mode, domain, user_roles)
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)).isoformat()
        
        cache_entry = {
            "data": data,
            "expires_at": expires_at,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.cache_backend == "memory":
            self.memory_cache[cache_key] = cache_entry
            # Limit memory cache size
            if len(self.memory_cache) > 1000:
                # Remove oldest entries
                sorted_keys = sorted(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k].get("cached_at", "")
                )
                for key in sorted_keys[:100]:
                    del self.memory_cache[key]
        
        elif self.cache_backend == "file":
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f)
        
        elif self.cache_backend == "redis" and self.redis_client:
            try:
                self.redis_client.setex(
                    f"query_cache:{cache_key}",
                    self.ttl_seconds,
                    json.dumps(cache_entry)
                )
            except Exception:
                pass
    
    def clear(self):
        """Clear all cache"""
        if self.cache_backend == "memory":
            self.memory_cache.clear()
        elif self.cache_backend == "file":
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        elif self.cache_backend == "redis" and self.redis_client:
            try:
                keys = self.redis_client.keys("query_cache:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass

