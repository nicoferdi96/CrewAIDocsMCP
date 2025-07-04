"""
Cache service for storing and retrieving documentation data.
"""

import time
from typing import Any, Optional
from lru import LRU


class CacheService:
    """
    LRU cache service with TTL support for caching documentation content.
    """
    
    def __init__(self, max_size: int = 104857600, ttl: int = 3600):
        """
        Initialize cache service.
        
        Args:
            max_size: Maximum cache size in bytes
            ttl: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        # Estimate ~1KB per entry, so max_entries = max_size / 1024
        max_entries = max(100, max_size // 1024)
        self._cache = LRU(max_entries)
        self._timestamps = {}
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
            
        # Check if expired
        if key in self._timestamps:
            if time.time() - self._timestamps[key] > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
                
        return self._cache[key]
        
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
        
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
        
    def size(self) -> int:
        """Get number of items in cache."""
        return len(self._cache)