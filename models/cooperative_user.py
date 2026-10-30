import uuid
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.enums import UserType
from models.user import User


class CooperativeUser(User):
    __tablename__ = "cooperative_user"

    cooperative_user_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(150), nullable=False)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    cooperative = relationship("Cooperative", back_populates="users")

    assignments = relationship(
        "AgentAssignment",
        foreign_keys="AgentAssignment.user_id",
        back_populates="agent",
    )
    created_assignments = relationship(
        "AgentAssignment",
        foreign_keys="AgentAssignment.assigned_by_user_id",
        back_populates="assigned_by",
    )
    produce_records = relationship("ProduceRecord", back_populates="agent")
    created_prices = relationship("ProducePrice", back_populates="created_by")
    initiated_payments = relationship(
        "PaymentTransaction",
        foreign_keys="PaymentTransaction.user_id",
        back_populates="initiated_by",
    )
    approved_payments = relationship(
        "PaymentTransaction",
        foreign_keys="PaymentTransaction.approved_by",
        back_populates="approved_by_user",
    )
    created_tasks = relationship("Task", foreign_keys="Task.created_by_user_id", back_populates="created_by")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to_user_id", back_populates="assigned_to")
    audit_events = relationship("AuditLog", back_populates="user")
    user = relationship(
        "User",
        back_populates="cooperative_user",
        foreign_keys=[user_id],
    )
    __mapper_args__ = {
        "polymorphic_identity": UserType.cooperative_agent,
        "inherit_condition": user_id == User.user_id,
    }
