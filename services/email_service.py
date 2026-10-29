import smtplib
from email.message import EmailMessage

from core.config import settings


def _send_email(message: EmailMessage) -> None:
    sender = settings.SMTP_FROM_EMAIL or settings.SMTP_EMAIL

    if not sender or not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL, SMTP_PASSWORD, and a sender email must be configured.")

    message["From"] = sender

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(message)


def send_login_otp(email: str, otp: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Your Umucyo login verification code"
    message["To"] = email
    message.set_content(
        f"Your Umucyo login verification code is {otp}.\n\n"
        f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not attempt to log in, ignore this email."
    )

    _send_email(message)


def send_invitation_email(
    email: str,
    first_name: str,
    link: str,
    purpose: str = "invitation",
) -> bool:
    message = EmailMessage()
    message["Subject"] = "Your Umucyo account invitation"
    message["To"] = email
    message.set_content(
        f"Hello {first_name},\n\n"
        f"You have received an Umucyo {purpose} invitation.\n\n"
        f"Use the following link to continue setting up your account:\n{link}\n\n"
        "If you were not expecting this invitation, you can ignore this email."
    )

    _send_email(message)
    return True
