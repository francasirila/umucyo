from uuid import uuid4

import pytest

from core import security
from core.config import settings
from models.enums import UserRole


def test_hash_and_verify_password():
    hashed = security.hash_password("SecurePassword123")
    assert hashed.startswith("pbkdf2_sha256$")
    assert security.verify_password("SecurePassword123", hashed)
    assert not security.verify_password("WrongPassword123", hashed)


def test_hashes_use_unique_salts():
    assert security.hash_password("SecurePassword123") != security.hash_password("SecurePassword123")


def test_get_password_hash_is_alias():
    assert security.verify_password("SecurePassword123", security.get_password_hash("SecurePassword123"))


@pytest.mark.parametrize("password", ["short", "x" * 129, ""])
def test_hash_password_rejects_invalid_length(password):
    with pytest.raises(ValueError):
        security.hash_password(password)


@pytest.mark.parametrize("bad_hash", [None, "", "garbage", "md5$1$a$b", "pbkdf2_sha256$x$y$z"])
def test_verify_password_handles_bad_hashes(bad_hash):
    assert security.verify_password("anything", bad_hash) is False


def test_token_round_trip():
    token = security.create_access_token("user-1", UserRole.admin)
    payload = security.decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["jti"]


def test_tampered_payload_rejected():
    first, second, signature = security.create_access_token("user-1", "admin").split(".")
    forged = security._b64(b'{"sub":"user-1","role":"admin","exp":99999999999}')
    with pytest.raises(ValueError):
        security.decode_access_token(f"{first}.{forged}.{signature}")


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    token = security.create_access_token("user-1", "admin")
    with pytest.raises(ValueError):
        security.decode_access_token(token)


@pytest.mark.parametrize("token", ["", "abc", "a.b", "a.b.c.d"])
def test_malformed_tokens_rejected(token):
    with pytest.raises(ValueError):
        security.decode_access_token(token)


def test_garbage_bearer_token_returns_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_token_for_unknown_user_returns_401(client):
    token = security.create_access_token(str(uuid4()), "admin")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_with_wrong_role_claim_returns_401(client, auth_headers):
    user_id = client.get("/auth/me", headers=auth_headers).json()["user_id"]
    forged = security.create_access_token(user_id, "agent")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
