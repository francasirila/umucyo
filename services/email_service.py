import smtplib
from email.message import EmailMessage

from core.config import settings
from services.email_templates import render_invitation_email, render_otp_email


def _send_email(message: EmailMessage) -> None:
    sender = settings.SMTP_FROM_EMAIL or settings.SMTP_EMAIL

    if not sender or not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL, SMTP_PASSWORD, and a sender email must be configured.")

    message["From"] = sender

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(message)


def _build_message(to: str, subject: str, text: str, html: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["To"] = to
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


def send_login_otp(email: str, otp: str, name: str = "") -> None:
    subject, text, html = render_otp_email(
        otp, name, minutes=settings.OTP_EXPIRE_MINUTES
    )
    _send_email(_build_message(email, subject, text, html))


def send_invitation_email(
    email: str,
    first_name: str,
    link: str,
    purpose: str = "invitation",
    collection_point: str = "",
) -> bool:
    subject, text, html = render_invitation_email(
        link,
        first_name,
        collection_point=collection_point,
        expires_hours=settings.invitation_expire_hours,
    )
    _send_email(_build_message(email, subject, text, html))
    return True