"""Two-level caching system: SQLite + in-memory."""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import aiosqlite
from cachetools import TTLCache


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache using cachetools TTLCache."""

    def __init__(self, maxsize: int = 1000, default_ttl: int = 3600):
        """
        Initialize in-memory cache.

        Args:
            maxsize: Maximum number of entries in cache
            default_ttl: Default TTL in seconds
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        """Get value from in-memory cache."""
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in in-memory cache (TTL handled by TTLCache)."""
        async with self._lock:
            self._cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from in-memory cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all in-memory cache entries."""
        async with self._lock:
            self._cache.clear()


class SQLiteCache(CacheBackend):
    """SQLite-based persistent cache."""

    def __init__(self, db_path: Path):
        """
        Initialize SQLite cache.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(str(self.db_path))
            await self._create_schema()
        return self._connection

    async def _create_schema(self) -> None:
        """Create cache table schema if not exists."""
        async with self._lock:
            conn = await self._get_connection()
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)
            await conn.commit()

    async def get(self, key: str) -> Optional[str]:
        """Get value from SQLite cache if not expired."""
        async with self._lock:
            conn = await self._get_connection()
            now = int(time.time())

            cursor = await conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > ?",
                (key, now),
            )
            row = await cursor.fetchone()
            await cursor.close()

            if row:
                return row[0]
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in SQLite cache with TTL."""
        async with self._lock:
            conn = await self._get_connection()
            now = int(time.time())
            expires_at = now + ttl_seconds

            await conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, value, now, expires_at),
            )
            await conn.commit()

    async def delete(self, key: str) -> None:
        """Delete value from SQLite cache."""
        async with self._lock:
            conn = await self._get_connection()
            await conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            await conn.commit()

    async def clear(self) -> None:
        """Clear all SQLite cache entries."""
        async with self._lock:
            conn = await self._get_connection()
            await conn.execute("DELETE FROM cache")
            await conn.commit()

    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache. Returns number of deleted entries."""
        async with self._lock:
            conn = await self._get_connection()
            now = int(time.time())

            cursor = await conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at <= ?", (now,)
            )
            count_row = await cursor.fetchone()
            count = count_row[0] if count_row else 0
            await cursor.close()

            await conn.execute("DELETE FROM cache WHERE expires_at <= ?", (now,))
            await conn.commit()

            return count

    async def get_cache_size(self) -> int:
        """Get current cache size in bytes."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None


class TwoLevelCacheManager:
    """
    Two-level cache manager combining in-memory and SQLite caches.

    Workflow:
    1. Check in-memory cache (fast)
    2. If miss -> check SQLite cache (persistent)
    3. If miss -> compute value -> save to both levels
    """

    def __init__(
        self,
        sqlite_cache: SQLiteCache,
        memory_cache: InMemoryCache,
    ):
        """
        Initialize two-level cache manager.

        Args:
            sqlite_cache: SQLite persistent cache backend
            memory_cache: In-memory fast cache backend
        """
        self.sqlite = sqlite_cache
        self.memory = memory_cache

    @staticmethod
    def make_key(prefix: str, *args: Any) -> str:
        """
        Generate cache key from prefix and arguments.

        Args:
            prefix: Key prefix (e.g., "cadastre", "geocode")
            args: Additional key components

        Returns:
            Cache key string
        """
        # For long strings (like addresses), use hash
        processed_args = []
        for arg in args:
            if isinstance(arg, str) and len(arg) > 50:
                # Hash long strings
                hash_value = hashlib.sha256(arg.encode()).hexdigest()[:16]
                processed_args.append(hash_value)
            else:
                processed_args.append(str(arg))

        return f"{prefix}:{':'.join(processed_args)}"

    async def get(self, key: str) -> Optional[dict]:
        """
        Get value from cache (memory -> SQLite).

        Args:
            key: Cache key

        Returns:
            Cached value as dict or None if not found
        """
        # Level 1: Check in-memory cache
        memory_value = await self.memory.get(key)
        if memory_value:
            return json.loads(memory_value)

        # Level 2: Check SQLite cache
        sqlite_value = await self.sqlite.get(key)
        if sqlite_value:
            # Promote to memory cache
            await self.memory.set(key, sqlite_value, ttl_seconds=3600)
            return json.loads(sqlite_value)

        return None

    async def set(
        self,
        key: str,
        value: dict,
        ttl_seconds: int,
        memory_only: bool = False,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (dict)
            ttl_seconds: Time to live in seconds
            memory_only: If True, only cache in memory (for short-lived data)
        """
        json_value = json.dumps(value, ensure_ascii=False)

        # Always set in memory for fast access
        await self.memory.set(key, json_value, ttl_seconds)

        # Set in SQLite for persistence (unless memory_only)
        if not memory_only:
            await self.sqlite.set(key, json_value, ttl_seconds)

    async def delete(self, key: str) -> None:
        """Delete value from both cache levels."""
        await self.memory.delete(key)
        await self.sqlite.delete(key)

    async def clear(self) -> None:
        """Clear both cache levels."""
        await self.memory.clear()
        await self.sqlite.clear()

    async def cleanup(self) -> int:
        """Clean up expired entries from SQLite cache. Returns number of deleted entries."""
        return await self.sqlite.cleanup_expired()

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        cache_size = await self.sqlite.get_cache_size()
        return {
            "sqlite_size_bytes": cache_size,
            "sqlite_size_mb": round(cache_size / (1024 * 1024), 2),
            "memory_entries": len(self.memory._cache),
        }

    async def close(self) -> None:
        """Close cache connections."""
        await self.sqlite.close()
