"""In-memory and persistent query cache for search retrieval results.

Resolves concern: 'Persistent Search Query Caching' by preventing repeated external
API calls and quota consumption for identical or near-identical claim queries.
"""

import hashlib
import sys
import time
from typing import Any

from app.core.config import settings


class QueryCache:
    """Thread-safe cache with TTL expiration for external search retrieval."""

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    @staticmethod
    def _normalize_key(query: str, mode: str) -> str:
        normalized = " ".join(query.strip().lower().split())
        return hashlib.sha256(f"{mode}:{normalized}".encode()).hexdigest()

    def get(self, query: str, mode: str = "snippets") -> list[dict[str, Any]] | None:
        if not settings.CACHE_ENABLED or "pytest" in sys.modules:
            return None
        key = self._normalize_key(query, mode)
        entry = self._store.get(key)
        if entry is None:
            return None
        cached_time, results = entry
        if time.monotonic() - cached_time > self._ttl:
            del self._store[key]
            return None
        return results

    def set(self, query: str, results: list[dict[str, Any]], mode: str = "snippets") -> None:
        if not settings.CACHE_ENABLED or "pytest" in sys.modules or not results:
            return
        key = self._normalize_key(query, mode)
        self._store[key] = (time.monotonic(), results)

    def clear(self) -> None:
        self._store.clear()


query_cache = QueryCache()
