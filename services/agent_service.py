import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import ServiceError
from core.utils import enum_value
from database import commit_session
from models.agent_invitation import AgentInvitation
from models.cooperative_user import CooperativeAgent, CooperativeUser
from models.enums import AccountStatus, UserRole
from schemas.users import AgentCreate, AgentUpdate
from services.access import get_active_point, require_admin
from services.audit_service import AuditService
from services.email_service import send_invitation_email


logger = logging.getLogger(__name__)

EMAIL_EXISTS = "An account with this email already exists."


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def register_agent(self, current_user, payload: AgentCreate) -> dict:
        cooperative_id = require_admin(current_user)
        email = str(payload.email).strip().lower()

        if self.db.scalar(select(CooperativeUser.user_id).where(CooperativeUser.email == email)):
            raise ServiceError(409, EMAIL_EXISTS)

        point = get_active_point(self.db, current_user, payload.collection_point_id)
        raw_token = secrets.token_urlsafe(32)

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

            self.db.add(
                AgentInvitation(
                    user_id=agent.user_id,
                    token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.invitation_expire_hours),
                )
            )
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
            commit_session(self.db)
            self.db.refresh(agent)
        except IntegrityError as exc:
            self.db.rollback()
            raise ServiceError(409, EMAIL_EXISTS) from exc

        link = f"{settings.frontend_url.rstrip('/')}/set-password?token={raw_token}"

        try:
            send_invitation_email(email, agent.first_name, link, "invitation")
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
        agent = self.db.get(CooperativeAgent, agent_id)
        if agent is None or agent.cooperative_id != cooperative_id:
            raise ServiceError(404, "Agent not found in your cooperative.")
        return agent

    def update_agent(self, current_user, agent_id: UUID, payload: AgentUpdate):
        cooperative_id = require_admin(current_user)
        agent = self.db.get(CooperativeAgent, agent_id)

        if agent is None or agent.cooperative_id != cooperative_id:
            raise ServiceError(404, "Agent not found in your cooperative.")

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
        commit_session(self.db)
        self.db.refresh(agent)
        return agent

    def resend_invitation(self, current_user, agent_id: UUID) -> dict:
        cooperative_id = require_admin(current_user)
        agent = self.db.get(CooperativeAgent, agent_id)

        if agent is None or agent.cooperative_id != cooperative_id:
            raise ServiceError(404, "Agent not found in your cooperative.")
        if agent.status != AccountStatus.pending:
            raise ServiceError(409, "This agent has already set a password.")

        raw_token = secrets.token_urlsafe(32)
        self.db.add(
            AgentInvitation(
                user_id=agent.user_id,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.invitation_expire_hours),
            )
        )
        commit_session(self.db)

        link = f"{settings.frontend_url.rstrip('/')}/set-password?token={raw_token}"
        try:
            send_invitation_email(agent.email, agent.first_name, link, "invitation")
            sent = True
        except Exception:
            logger.exception("Agent invitation resend failed")
            sent = False

        return {"message": "Invitation re-sent." if sent else "Email could not be sent.", "invitation_sent": sent}
