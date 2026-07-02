"""Отправка писем. В dev режиме печатает в консоль/лог; в prod — SMTP."""
import logging

from app.core.config import settings

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    if settings.email_backend == "console":
        logger.info("EMAIL → %s | %s\n%s", to, subject, body)
        return

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    send_email(
        to,
        "Подтверждение email",
        f"Добро пожаловать! Подтвердите адрес по ссылке:\n{link}",
    )


def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    send_email(
        to,
        "Сброс пароля",
        f"Для сброса пароля перейдите по ссылке:\n{link}",
    )
