import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}

def get_cache(key: str, ttl_seconds: int):
    item = _cache.get(key)
    if not item:
        return None
    ts, value = item
    if time.time() - ts > ttl_seconds:
        _cache.pop(key, None)
        return None
    return value

def set_cache(key: str, value: Any):
    _cache[key] = (time.time(), value)
