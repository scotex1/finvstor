"""
database/models.py — In-memory cache (NO SQLite on Render)

Render pe SQLite use mat karo — filesystem ephemeral hai.
Primary database = Firestore
Cache = in-memory Python dict (resets on redeploy — that's fine)

Local dev mein SQLite enable karna ho to:
  USE_SQLITE_CACHE=True in .env
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# IN-MEMORY CACHE (works on Render — no file system needed)
# ════════════════════════════════════════════════════════════

_memory_cache: dict = {}


def cache_set(key: str, data, ttl_minutes: int = 15):
    """Store value in memory with expiry."""
    _memory_cache[key] = {
        "data":    data,
        "expires": datetime.utcnow() + timedelta(minutes=ttl_minutes)
    }


def cache_get(key: str) -> Optional[any]:
    """Get value from memory cache. Returns None if missing or expired."""
    entry = _memory_cache.get(key)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires"]:
        del _memory_cache[key]
        return None
    return entry["data"]


def cache_delete(key: str):
    _memory_cache.pop(key, None)


def cache_clear():
    _memory_cache.clear()


def cache_stats() -> dict:
    valid = sum(
        1 for v in _memory_cache.values()
        if datetime.utcnow() < v["expires"]
    )
    return {"total_keys": len(_memory_cache), "valid_keys": valid}


# ════════════════════════════════════════════════════════════
# OPTIONAL SQLITE (local dev only — set USE_SQLITE_CACHE=True)
# ════════════════════════════════════════════════════════════

def get_db():
    """
    FastAPI dependency — returns None on Render (SQLite disabled).
    Cache handled by memory functions above.
    """
    return None

