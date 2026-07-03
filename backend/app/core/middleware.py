"""Middleware rate-limit для эндпоинтов авторизации (защита от перебора)."""
import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.services.rate_limit import allow_request

_PROTECTED = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
}


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._client: redis.Redis | None = None

    def _redis(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(settings.redis_url)
        return self._client

    async def dispatch(self, request: Request, call_next):
        if (
            settings.auth_rate_limit_enabled
            and request.method == "POST"
            and request.url.path in _PROTECTED
        ):
            forwarded = request.headers.get("x-forwarded-for")
            ip = (
                forwarded.split(",")[0].strip()
                if forwarded
                else (request.client.host if request.client else "unknown")
            )
            key = f"rl:auth:{ip}:{request.url.path}"
            try:
                allowed = allow_request(
                    self._redis(),
                    key,
                    settings.auth_rate_limit_max,
                    settings.auth_rate_limit_window_seconds,
                )
            except Exception:  # noqa: BLE001 — Redis недоступен → пропускаем (fail-open)
                allowed = True
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Слишком много запросов, попробуйте позже"},
                )
        return await call_next(request)
