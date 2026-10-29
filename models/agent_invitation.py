import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.types import Uuid

from database import Base


class AgentInvitation(Base):
    __tablename__ = "agent_invitation"

    invitation_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("cooperative_user.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
