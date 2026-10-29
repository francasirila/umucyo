import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.enums import UserRole
from models.user import User


class CooperativeUser(User):
    __tablename__ = "cooperative_user"

    cooperative_user_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    password_hash = Column(String(255), nullable=True)
    email = Column(String(150), nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=True)
    registered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    cooperative = relationship("Cooperative", back_populates="cooperative_users")
    collection_point = relationship("CollectionPoint", back_populates="cooperative_users", foreign_keys=[collection_point_id])
    agent_assignment = relationship("AgentAssignment", foreign_keys="AgentAssignment.user_id", back_populates="agent")
    assigned_by_assignments = relationship(
        "AgentAssignment", foreign_keys="AgentAssignment.assigned_by_user_id", back_populates="assigned_by"
    )
    created_prices = relationship("ProducePrice", back_populates="created_by")
    initiated_payments = relationship(
        "PaymentTransaction", foreign_keys="PaymentTransaction.user_id", back_populates="initiated_by"
    )
    approved_payments = relationship(
        "PaymentTransaction", foreign_keys="PaymentTransaction.approved_by", back_populates="approved_by_user"
    )
    created_tasks = relationship("Task", foreign_keys="Task.created_by_user_id", back_populates="created_by")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to_user_id", back_populates="assigned_to")
    audit_log = relationship("AuditLog", back_populates="user")
    produce_records = relationship("ProduceRecord", back_populates="cooperative_user")

    __mapper_args__ = {
        "polymorphic_abstract": True,
        "inherit_condition": user_id == User.user_id,
    }


class CooperativeAdmin(CooperativeUser):
    __mapper_args__ = {
        "polymorphic_identity": UserRole.admin,
    }


class CooperativeAgent(CooperativeUser):
    __mapper_args__ = {
        "polymorphic_identity": UserRole.agent,
    }
