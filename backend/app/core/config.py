"""Настройки приложения (читаются из переменных окружения / .env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Приложение
    app_name: str = "Online Programmer"
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"

    # Хранилища
    database_url: str = "postgresql+psycopg2://app:app@db:5432/online_programmer"
    redis_url: str = "redis://redis:6379/0"

    # JWT / безопасность
    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # TTL одноразовых токенов (в часах)
    email_verification_ttl_hours: int = 24
    password_reset_ttl_hours: int = 2

    # Email: console = печать в лог (dev), smtp = реальная отправка
    email_backend: str = "console"
    email_from: str = "no-reply@online-programmer.local"
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
