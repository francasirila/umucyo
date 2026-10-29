import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.utils import enum_value
from database import get_db
from models.enums import AccountStatus
from models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must contain between 8 and 128 characters.")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000$" + _b64(salt) + "$" + _b64(digest)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, rounds, salt, expected = password_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(rounds))
        return hmac.compare_digest(actual, _unb64(expected))

    except (ValueError, TypeError):
        return False


def _sign(signing_input: str) -> str:
    return _b64(
        hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
    )


def create_access_token(user_id: str, role) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "role": str(enum_value(role)),
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}

    first = _b64(json.dumps(header, separators=(",", ":")).encode())
    second = _b64(json.dumps(payload, separators=(",", ":")).encode())

    return f"{first}.{second}.{_sign(f'{first}.{second}')}"


def decode_access_token(token: str) -> dict:
    try:
        first, second, signature = token.split(".")

        if not hmac.compare_digest(_unb64(_sign(f"{first}.{second}")), _unb64(signature)):
            raise ValueError("Invalid signature")

        header = json.loads(_unb64(first))
        payload = json.loads(_unb64(second))

        if header.get("alg") != "HS256":
            raise ValueError("Unsupported algorithm")

        if int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Expired token")

        return payload

    except Exception as exc:
        raise ValueError("Invalid or expired token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        user = db.get(User, UUID(payload["sub"]))
    except Exception as exc:
        raise unauthorized from exc

    if user is None or str(enum_value(user.role)) != payload.get("role"):
        raise unauthorized

    if user.status != AccountStatus.active:
        raise HTTPException(status_code=403, detail="Account is inactive.")

    return user
