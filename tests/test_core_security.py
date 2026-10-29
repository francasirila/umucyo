from core.security import hash_password, verify_password
from core.utils import enum_value
from models.enums import UserRole


def test_hash_password_and_verify_password():
    raw = "StrongPassword123"
    hashed = hash_password(raw)

    assert hashed is not None
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_enum_value_returns_underlying_value():
    assert enum_value(UserRole.admin) == "admin"
    assert enum_value(UserRole.agent) == "agent"
