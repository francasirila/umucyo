import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.exceptions import ServiceError
from core.security import create_access_token, get_password_hash, verify_password
from core.utils import ensure_aware, enum_value, utcnow
from models.agent_invitation import AgentInvitation
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeAdmin, CooperativeAgent, CooperativeUser
from models.enums import AccountStatus, UserRole
from models.login_otp import LoginOTP
from models.user import User
from services.audit_service import AuditService
from services.email_service import send_login_otp

MAX_OTP_ATTEMPTS = 5
USER_MODELS = {UserRole.admin: CooperativeAdmin, UserRole.agent: CooperativeAgent}
INVALID_INVITATION = "This invitation link is invalid or has expired."
OTP_SEND_FAILED = "Unable to send the login verification code. Please try again."


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

        self.db.query(LoginOTP).filter(
            LoginOTP.user_id == user.user_id,
            LoginOTP.consumed_at.is_(None),
        ).delete(synchronize_session=False)

        self.db.add(
            LoginOTP(
                user_id=user.user_id,
                otp_hash=self._hash(code),
                expires_at=utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
                attempts=0,
            )
        )
        commit_session(self.db)

        try:
            send_login_otp(str(user.email), code)
        except Exception as exc:
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

        otp = self.db.scalar(
            select(LoginOTP)
            .where(LoginOTP.user_id == user.user_id, LoginOTP.consumed_at.is_(None))
            .order_by(LoginOTP.created_at.desc())
        )
        if otp is None:
            raise ServiceError(401, "Invalid email or OTP.")

        if otp.attempts >= MAX_OTP_ATTEMPTS:
            raise ServiceError(429, "Too many incorrect codes. Request a new code.")

        if ensure_aware(otp.expires_at) <= utcnow():
            raise ServiceError(401, "OTP has expired.")

        if not secrets.compare_digest(self._hash(code), otp.otp_hash):
            otp.attempts += 1
            commit_session(self.db)
            raise ServiceError(401, "Invalid email or OTP.")

        if user.status != AccountStatus.active:
            raise ServiceError(403, "This account is inactive.")

        otp.consumed_at = utcnow()
        token = create_access_token(str(user.user_id), enum_value(user.role))
        self.audit.record(user, "verify_login_otp", "user", user.user_id)
        commit_session(self.db)

        return {"access_token": token, "token_type": "bearer", "user": user}

    def set_password(self, token, password):
        invitation = self.db.scalar(select(AgentInvitation).where(AgentInvitation.token_hash == self._hash(token)))
        now = utcnow()

        if invitation is None or invitation.accepted_at is not None or ensure_aware(invitation.expires_at) <= now:
            raise ServiceError(400, INVALID_INVITATION)

        user = self.db.get(CooperativeUser, invitation.user_id)
        if user is None:
            raise ServiceError(400, INVALID_INVITATION)

        try:
            user.password_hash = get_password_hash(password)
        except ValueError as exc:
            raise ServiceError(422, str(exc)) from exc

        invitation.accepted_at = now
        user.status = AccountStatus.active
        user.email_verified_at = now

        self.audit.record(user, "set_password", "user", user.user_id)
        commit_session(self.db)

        return {"message": "Password set successfully. You can now sign in."}

    def logout(self, user):
        self.audit.record(user, "logout", "user", user.user_id)
        commit_session(self.db)
        return {"message": "Logged out successfully."}
