"""Глобальный rate-limiter на Redis: не чаще 1 запроса в окно (для CF API).

Реализация — «слот» через SET key NX PX: пока ключ жив, новый запрос не проходит.
Так лимит соблюдается глобально, даже при нескольких воркерах.
"""
import time

import redis

from app.core.config import settings


class RedisRateLimiter:
    def __init__(self, client: redis.Redis, key: str = "cf:ratelimit", window_ms: int | None = None):
        self.client = client
        self.key = key
        self.window_ms = window_ms if window_ms is not None else settings.cf_rate_limit_ms

    def acquire(self, block: bool = True, poll_seconds: float = 0.05) -> bool:
        while True:
            if self.client.set(self.key, "1", nx=True, px=self.window_ms):
                return True
            if not block:
                return False
            time.sleep(poll_seconds)


_client: redis.Redis | None = None


def get_default_limiter() -> RedisRateLimiter:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url)
    return RedisRateLimiter(_client)
