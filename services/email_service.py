import smtplib
import ssl
from email.message import EmailMessage

from core.config import settings
from services.email_templates import render_invitation_email, render_otp_email


def _send_email(message: EmailMessage) -> None:
    sender = settings.SMTP_FROM_EMAIL or settings.SMTP_EMAIL

    if not sender or not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL, SMTP_PASSWORD, and a sender email must be configured.")

    if not settings.SMTP_HOST or not settings.SMTP_PORT:
        raise RuntimeError("SMTP_HOST and SMTP_PORT must be configured.")

    message["From"] = sender

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(message)


def _build_message(email: str, subject: str, text: str, html: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["To"] = email
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


def send_login_otp(email: str, otp: str, first_name: str = "") -> bool:
    subject, text, html = render_otp_email(
        code=otp,
        name=first_name,
        minutes=settings.OTP_EXPIRE_MINUTES,
    )
    message = _build_message(email=email, subject=subject, text=text, html=html)
    _send_email(message)
    return True


def send_invitation_email(email: str, first_name: str, link: str, purpose: str = "invitation") -> bool:
    _ = purpose
    subject, text, html = render_invitation_email(
        link=link,
        name=first_name,
        collection_point="",
        expires_hours=settings.password_setup_expire_hours,
    )
    message = _build_message(email=email, subject=subject, text=text, html=html)
    _send_email(message)
    return True


def send_password_setup_email(
    email: str,
    first_name: str,
    link: str,
    collection_point: str = "",
) -> bool:
    subject, text, html = render_invitation_email(
        link=link,
        name=first_name,
        collection_point=collection_point,
        expires_hours=settings.password_setup_expire_hours,
    )
    message = _build_message(email=email, subject=subject, text=text, html=html)
    _send_email(message)
    return True
