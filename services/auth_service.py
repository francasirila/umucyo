import hashlib
import secrets
import logging
from datetime import datetime, timezone
import threading
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from core.config import settings
from core.exceptions import ServiceError
from core.security import create_access_token, get_password_hash, verify_password
from core.utils import ensure_aware, enum_value, utcnow
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeAdmin, CooperativeAgent, CooperativeUser
from models.enums import AccountStatus, UserRole
from models.user import User
from services.audit_service import AuditService
from services.email_service import send_login_otp
from services.email_service import send_invitation_email
from core.security import hash_password

MAX_OTP_ATTEMPTS = 5
USER_MODELS = {UserRole.admin: CooperativeAdmin, UserRole.agent: CooperativeAgent}
OTP_SEND_FAILED = "Unable to send the login verification code. Please try again."
INVALID_INVITATION = "This invitation link is invalid or has expired."
RESET_MESSAGE = "If an account exists for this email, a reset link has been sent."

_otp_store = {}
_otp_lock = threading.Lock()

logger = logging.getLogger(__name__)


def _otp_set(key, otp_hash, ttl_minutes):
    with _otp_lock:
        _otp_store[key] = {
            "hash": otp_hash,
            "expires_at": utcnow() + timedelta(minutes=ttl_minutes),
            "attempts": 0,
        }


def _otp_get(key):
    with _otp_lock:
        entry = _otp_store.get(key)
        if entry is None:
            return None
        if ensure_aware(entry["expires_at"]) <= utcnow():
            del _otp_store[key]
            return None
        return entry


def _otp_add_attempt(key):
    with _otp_lock:
        if key in _otp_store:
            _otp_store[key]["attempts"] += 1


def _otp_delete(key):
    with _otp_lock:
        _otp_store.pop(key, None)


def commit_session(db):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


class AuthService:
    def __init__(self, db):
        self.db = db
        self.audit = AuditService(db)

    @staticmethod
    def _email(email):
        return str(email).strip().lower()

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _find_user(self, email):
        return self.db.scalar(select(CooperativeUser).where(CooperativeUser.email == self._email(email)))

    def _new_user(self, first_name, last_name, role, cooperative_id, email, password_hash=None, status=AccountStatus.active):
        model = USER_MODELS.get(role)
        if model is None:
            raise ValueError(f"Invalid cooperative role provided: {role}")

        user = model(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            user_type=role,
            status=status,
            email=self._email(email),
            password_hash=password_hash,
            cooperative_id=cooperative_id,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def _issue_otp(self, user):
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        key = str(user.user_id)

        _otp_set(key, self._hash(code), settings.OTP_EXPIRE_MINUTES)

        try:
            send_login_otp(str(user.email), code)
        except Exception as exc:
            logger.exception("Failed to send login OTP to %s", user.email)
            _otp_delete(key)
            raise ServiceError(503, OTP_SEND_FAILED) from exc

            
    def register_cooperative(self, payload):
        email = self._email(payload.email)
        name = payload.cooperative_name.strip()

        if self._find_user(email):
            raise ServiceError(409, "An account with this email already exists.")

        if self.db.scalar(select(Cooperative).where(Cooperative.cooperative_name == name)):
            raise ServiceError(409, "A cooperative with this name already exists.")

        try:
            cooperative = Cooperative(
                cooperative_name=name,
                email=email,
            )
            self.db.add(cooperative)
            self.db.flush()

            user = self._new_user(
                payload.first_name,
                payload.last_name,
                UserRole.admin,
                cooperative.cooperative_id,
                email,
                get_password_hash(payload.password),
            )

            self.audit.record(
                user,
                "register_cooperative",
                "cooperative",
                cooperative.cooperative_id,
                new_values={"cooperative_name": cooperative.cooperative_name},
            )
            commit_session(self.db)
            self.db.refresh(user)

            return {
                "cooperative_id": cooperative.cooperative_id,
                "message": "Cooperative and administrator account created successfully.",
                "admin": user,
            }
        except IntegrityError as exc:
            self.db.rollback()
            raise ServiceError(409, "Registration conflicts with an existing record.") from exc

    def bootstrap_admin(self, payload, supplied_key):
        configured = settings.bootstrap_secret

        if not configured or not secrets.compare_digest(configured.encode(), (supplied_key or "").encode()):
            raise ServiceError(403, "Invalid bootstrap key.")

        existing = self.db.scalar(select(User.user_id).where(User.user_type == UserRole.admin).limit(1))
        if existing:
            raise ServiceError(409, "Bootstrap is disabled because an administrator already exists.")

        return self.register_cooperative(payload)

    def login(self, email, password):
        user = self._find_user(email)

        if user is None or not verify_password(password, user.password_hash):
            raise ServiceError(401, "Invalid email or password.")

        if user.status != AccountStatus.active:
            raise ServiceError(403, "This account is inactive.")

        self._issue_otp(user)

        self.audit.record(user, "login", "user", user.user_id, new_values={"otp_required": True})
        commit_session(self.db)

        return {
            "requires_otp": True,
            "message": "Login requires OTP verification.",
            "email": user.email,
        }

    def resend_login_otp(self, email):
        user = self._find_user(email)

        if user is None:
            raise ServiceError(404, "Account not found.")

        if user.status != AccountStatus.active:
            raise ServiceError(403, "This account is inactive.")

        self._issue_otp(user)

        return {
            "requires_otp": True,
            "message": "A new verification code has been sent to your email.",
            "email": user.email,
        }

    def verify_login_otp(self, email, code):
        user = self._find_user(email)
        if user is None:
            raise ServiceError(401, "Invalid email or OTP.")

        key = str(user.user_id)
        entry = _otp_get(key)
        if entry is None:
            raise ServiceError(401, "Invalid or expired OTP.")

        if entry["attempts"] >= MAX_OTP_ATTEMPTS:
            _otp_delete(key)
            raise ServiceError(429, "Too many incorrect codes. Request a new code.")

        if not secrets.compare_digest(self._hash(code), entry["hash"]):
            _otp_add_attempt(key)
            raise ServiceError(401, "Invalid email or OTP.")

        if user.status != AccountStatus.active:
            raise ServiceError(403, "This account is inactive.")

        _otp_delete(key)  # single use

        token = create_access_token(str(user.user_id), enum_value(user.role))
        self.audit.record(user, "verify_login_otp", "user", user.user_id)
        commit_session(self.db)

        return {"access_token": token, "token_type": "bearer", "user": user}

    def set_password(self, token: str, password: str) -> dict:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = self.db.scalar(select(CooperativeUser).where(CooperativeUser.password_setup_token_hash == token_hash))

        expires = user.password_setup_expires_at if user else None
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if user is None or expires is None or expires < datetime.now(timezone.utc):
            raise ServiceError(400, "This invitation link is invalid or has expired.")

        user.password_hash = hash_password(password)  # use your existing hashing helper
        user.status = AccountStatus.active
        user.password_setup_token_hash = None
        user.password_setup_expires_at = None
        self.db.commit()
        return {"message": "Password set successfully."}

    def logout(self, user):
        self.audit.record(user, "logout", "user", user.user_id)
        commit_session(self.db)
        return {"message": "Logged out successfully."}

    def forgot_password(self, email: str) -> dict:
        user = self.db.scalar(select(CooperativeUser).where(func.lower(CooperativeUser.email) == email.strip().lower()))

        if user is None or user.status != AccountStatus.active:
            return {"message": RESET_MESSAGE}

        raw_token = secrets.token_urlsafe(32)
        user.password_setup_token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        user.password_setup_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=getattr(settings, "password_reset_expire_minutes", 60)
        )
        self.db.commit()

        link = f"{settings.frontend_url.rstrip('/')}/set-password?token={raw_token}"
        try:
            send_invitation_email(user.email, user.first_name, link, "reset")
        except Exception:
            logger.exception("Password reset email failed")

        return {"message": RESET_MESSAGE}
