import uuid
from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class AgentAssignment(Base):
    __tablename__ = "agent_assignment"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=False)
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("CooperativeUser", foreign_keys=[user_id], back_populates="agent_assignment")
    assigned_by = relationship("CooperativeUser", foreign_keys=[assigned_by_user_id], back_populates="assigned_by_assignments")
    collection_point = relationship("CollectionPoint", back_populates="assignments")
