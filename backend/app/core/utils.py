"""Мелкие переиспользуемые утилиты."""


def normalize_email(email: str) -> str:
    return email.strip().lower()
