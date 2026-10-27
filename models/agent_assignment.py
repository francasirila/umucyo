import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class AgentAssignment(Base):
    __tablename__ = "agent_assignment"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=False,
        index=True,
    )
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("User", back_populates="agent_assignments", foreign_keys=[user_id])
    assigned_by = relationship("User", back_populates="assignments_made", foreign_keys=[assigned_by_user_id])
    collection_point = relationship("CollectionPoint", back_populates="agent_assignments")
