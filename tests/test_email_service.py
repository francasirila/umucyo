import pytest

from core.config import settings
from services import email_service


class FakeSMTP:
    instances = []

    def __init__(self, host, port):
        self.host, self.port = host, port
        self.started = False
        self.credentials = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started = True

    def login(self, user, password):
        self.credentials = (user, password)

    def send_message(self, message):
        self.sent.append(message)


@pytest.fixture()
def smtp(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(settings, "SMTP_EMAIL", "sender@example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    return FakeSMTP


def test_send_login_otp_builds_and_sends_message(smtp):
    email_service.send_login_otp("user@example.com", "123456")

    server = smtp.instances[0]
    assert (server.host, server.port) == ("smtp.test", 2525)
    assert server.started
    assert server.credentials == ("sender@example.com", "secret")

    message = server.sent[0]
    assert message["To"] == "user@example.com"
    assert message["From"] == "sender@example.com"
    assert "123456" in message.get_content()


def test_send_invitation_email_contains_name_and_link(smtp):
    result = email_service.send_invitation_email("agent@example.com", "Alice", "http://x/set-password?token=abc", "invitation")

    message = smtp.instances[0].sent[0]
    assert result is True
    assert "Alice" in message.get_content()
    assert "http://x/set-password?token=abc" in message.get_content()


def test_from_email_overrides_login_address(smtp, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.com")
    email_service.send_login_otp("user@example.com", "123456")
    assert smtp.instances[0].sent[0]["From"] == "noreply@example.com"


@pytest.mark.parametrize("field", ["SMTP_EMAIL", "SMTP_PASSWORD"])
def test_missing_smtp_configuration_raises(smtp, monkeypatch, field):
    monkeypatch.setattr(settings, field, "")
    with pytest.raises(RuntimeError):
        email_service.send_login_otp("user@example.com", "123456")
    assert smtp.instances == []
