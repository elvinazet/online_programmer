"""Базовый класс моделей и общие примеси."""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# BIGINT в Postgres, но INTEGER в SQLite — иначе автоинкремент PK не работает
# в тестах на SQLite.
BigInt = BigInteger().with_variant(Integer, "sqlite")

# JSONB в Postgres, обычный JSON в SQLite (для тестов).
JsonB = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
