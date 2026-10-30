import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import ServiceError
from core.utils import enum_value
from models.agent_invitation import AgentInvitation
from models.collection_point import CollectionPoint
from models.cooperative_user import CooperativeAgent, CooperativeUser
from models.enums import AccountStatus, UserRole
from models.farmer import Farmer
from schemas.users import AgentCreate, AgentUpdate, FarmerCreate
from services.access import get_active_point, require_admin, require_staff, role_of
from services.audit_service import AuditService
from services.email_service import send_invitation_email
from services.sms_service import normalize_phone, send_sms

logger = logging.getLogger(__name__)

EMAIL_EXISTS = "An account with this email already exists."
PHONE_EXISTS = "A farmer with this phone number already exists."
FARMER_EXISTS = "A farmer with these details already exists."
AGENT_NOT_FOUND = "Agent not found in your cooperative."


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _new_invitation(user_id: UUID) -> tuple[str, AgentInvitation]:
        raw_token = secrets.token_urlsafe(32)
        invitation = AgentInvitation(
            user_id=user_id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.invitation_expire_hours),
        )
        return raw_token, invitation

    @staticmethod
    def _invitation_link(raw_token: str) -> str:
        return f"{settings.frontend_url.rstrip('/')}/set-password?token={raw_token}"

    def _get_agent_or_404(self, cooperative_id, agent_id: UUID) -> CooperativeAgent:
        agent = self.db.get(CooperativeAgent, agent_id)
        if agent is None or agent.cooperative_id != cooperative_id:
            raise ServiceError(404, AGENT_NOT_FOUND)
        return agent

    def register_agent(self, current_user, payload: AgentCreate) -> dict:
        cooperative_id = require_admin(current_user)
        email = str(payload.email).strip().lower()

        if self.db.scalar(select(CooperativeUser.user_id).where(func.lower(CooperativeUser.email) == email)):
            raise ServiceError(409, EMAIL_EXISTS)

        point = get_active_point(self.db, current_user, payload.collection_point_id)

        agent = CooperativeAgent(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            user_type=UserRole.agent,
            status=AccountStatus.pending,
            email=email,
            password_hash=None,
            cooperative_id=cooperative_id,
            collection_point_id=point.collection_point_id,
            registered_by_user_id=current_user.user_id,
        )

        try:
            self.db.add(agent)
            self.db.flush()

            raw_token, invitation = self._new_invitation(agent.user_id)
            self.db.add(invitation)

            self.audit.record(
                current_user,
                "register_agent",
                "user",
                agent.user_id,
                new_values={
                    "email": email,
                    "collection_point_id": str(point.collection_point_id),
                },
            )
            self.db.commit()
            self.db.refresh(agent)
        except IntegrityError as exc:
            self.db.rollback()
            raise ServiceError(409, EMAIL_EXISTS) from exc
        except Exception:
            self.db.rollback()
            raise

        try:
            send_invitation_email(email, agent.first_name, self._invitation_link(raw_token), "invitation")
            invitation_sent = True
        except Exception:
            logger.exception("Agent invitation email failed")
            invitation_sent = False

        message = (
            "Agent registered. An invitation email was sent."
            if invitation_sent
            else "Agent registered. Invitation email could not be sent; configure email delivery and resend the invitation."
        )
        return {"message": message, "agent": agent, "invitation_sent": invitation_sent}

    def list_agents(self, current_user, collection_point_id: UUID | None = None):
        cooperative_id = require_admin(current_user)
        stmt = select(CooperativeAgent).where(CooperativeAgent.cooperative_id == cooperative_id)
        if collection_point_id:
            stmt = stmt.where(CooperativeAgent.collection_point_id == collection_point_id)
        return list(self.db.scalars(stmt.order_by(CooperativeAgent.created_at.desc())))

    def get_agent(self, current_user, agent_id: UUID):
        cooperative_id = require_admin(current_user)
        return self._get_agent_or_404(cooperative_id, agent_id)

    def update_agent(self, current_user, agent_id: UUID, payload: AgentUpdate):
        cooperative_id = require_admin(current_user)
        agent = self._get_agent_or_404(cooperative_id, agent_id)

        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not changes:
            raise ServiceError(422, "Provide at least one field to update.")

        for key in ("first_name", "last_name"):
            if key in changes:
                changes[key] = changes[key].strip()

        old_values = {k: str(enum_value(getattr(agent, k))) for k in changes}

        for key, value in changes.items():
            setattr(agent, key, value)

        self.audit.record(
            current_user,
            "update_agent",
            "user",
            agent.user_id,
            old_values=old_values,
            new_values={k: str(enum_value(v)) for k, v in changes.items()},
        )
        self._commit()
        self.db.refresh(agent)
        return agent

    def resend_invitation(self, current_user, agent_id: UUID) -> dict:
        cooperative_id = require_admin(current_user)
        agent = self._get_agent_or_404(cooperative_id, agent_id)

        if agent.status != AccountStatus.pending:
            raise ServiceError(409, "This agent has already set a password.")

        raw_token, invitation = self._new_invitation(agent.user_id)
        self.db.add(invitation)
        self._commit()

        try:
            send_invitation_email(agent.email, agent.first_name, self._invitation_link(raw_token), "invitation")
            sent = True
        except Exception:
            logger.exception("Agent invitation resend failed")
            sent = False

        return {
            "message": "Invitation re-sent." if sent else "Email could not be sent.",
            "invitation_sent": sent,
        }

    def register_farmer(self, current_user, payload: FarmerCreate) -> dict:
        require_staff(current_user)
        point = get_active_point(self.db, current_user, payload.collection_point_id)
        phone = normalize_phone(payload.phone_number)

        if self.db.scalar(select(Farmer.user_id).where(Farmer.phone_number == phone)):
            raise ServiceError(409, PHONE_EXISTS)

        farmer = Farmer(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            user_type=UserRole.farmer,
            status=AccountStatus.active,
            phone_number=phone,
            collection_point_id=point.collection_point_id,
            registered_by_user_id=current_user.user_id,
            farmer_id=__import__('uuid').uuid4(),
        )

        try:
            self.db.add(farmer)
            self.db.flush()
            self.audit.record(
                current_user,
                "register_farmer",
                "user",
                farmer.user_id,
                new_values={
                    "phone_number": phone,
                    "collection_point_id": str(point.collection_point_id),
                },
            )
            self.db.commit()
            self.db.refresh(farmer)
        except IntegrityError as exc:
            self.db.rollback()
            raise ServiceError(409, FARMER_EXISTS) from exc
        except Exception:
            self.db.rollback()
            raise

        try:
            sms_sent = bool(
                send_sms(
                    phone,
                    f"Hello {farmer.first_name}, your Umucyo farmer account was "
                    "created successfully. You can now use Umucyo through USSD.",
                )
            )
        except Exception:
            logger.exception("Farmer confirmation SMS failed")
            sms_sent = False

        return {
            "message": "Farmer registered successfully.",
            "farmer": farmer,
            "sms_sent": sms_sent,
        }

    def _farmer_scope(self, current_user):
        cooperative_id = require_staff(current_user)
        stmt = (
            select(Farmer)
            .join(CollectionPoint, Farmer.collection_point_id == CollectionPoint.collection_point_id)
            .where(CollectionPoint.cooperative_id == cooperative_id)
        )
        if role_of(current_user) == UserRole.agent.value:
            stmt = stmt.where(Farmer.collection_point_id == current_user.collection_point_id)
        return stmt

    def list_farmers(self, current_user, collection_point_id: UUID | None = None):
        stmt = self._farmer_scope(current_user)
        if collection_point_id:
            stmt = stmt.where(Farmer.collection_point_id == collection_point_id)
        return list(self.db.scalars(stmt.order_by(Farmer.created_at.desc())))

    def get_farmer(self, current_user, farmer_id: UUID):
        farmer = self.db.scalar(self._farmer_scope(current_user).where(Farmer.user_id == farmer_id))
        if farmer is None:
            raise ServiceError(404, "Farmer not found.")
        return farmer
