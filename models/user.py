import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import AccountStatus, UserRole


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.AGENT)
    status = Column(
        Enum(AccountStatus, name="account_status"),
        nullable=False,
        default=AccountStatus.ACTIVE,
        server_default="active",
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    password_hash = Column(String(255), nullable=True)
    email = Column(String(150), nullable=True)
    id_number = Column(String(50), nullable=True)
    cooperative_location = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    cooperative_name = Column(String(150), nullable=True)
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=True,
        index=True,
    )
    registered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    farmer_collection_point = relationship("CollectionPoint", back_populates="farmers", foreign_keys=[collection_point_id])
    managed_collection_points = relationship(
        "CollectionPoint",
        back_populates="cooperative_admin",
        foreign_keys="CollectionPoint.cooperative_admin_id",
    )
    registered_by = relationship(
        "User",
        remote_side=[user_id],
        back_populates="registered_users",
        foreign_keys=[registered_by_user_id],
    )
    registered_users = relationship("User", back_populates="registered_by", foreign_keys=[registered_by_user_id])
    produce_records = relationship("ProduceRecord", back_populates="farmer", foreign_keys="ProduceRecord.farmer_id")
    farmer_produce_records = relationship("ProduceRecord", back_populates="agent", foreign_keys="ProduceRecord.user_id")
    farmer_payments = relationship(
        "PaymentTransaction",
        back_populates="farmer",
        foreign_keys="PaymentTransaction.farmer_id",
    )
    initiated_payments = relationship(
        "PaymentTransaction",
        back_populates="initiated_by",
        foreign_keys="PaymentTransaction.initiated_by_user_id",
    )
    approved_payments = relationship(
        "PaymentTransaction",
        back_populates="approved_by_user",
        foreign_keys="PaymentTransaction.approved_by",
    )
    farmer_messages = relationship("MessageLog", back_populates="farmer", foreign_keys="MessageLog.farmer_id")
    reviewed_messages = relationship(
        "MessageLog",
        back_populates="reviewed_by_user",
        foreign_keys="MessageLog.reviewed_by",
    )
    created_tasks = relationship("Task", back_populates="created_by", foreign_keys="Task.created_by_user_id")
    assigned_tasks = relationship("Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_user_id")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")
    created_prices = relationship(
        "ProducePrice",
        back_populates="created_by",
        foreign_keys="ProducePrice.created_by_user_id",
    )
    agent_assignments = relationship(
        "AgentAssignment",
        back_populates="agent",
        foreign_keys="AgentAssignment.user_id",
    )
    assignments_made = relationship(
        "AgentAssignment",
        back_populates="assigned_by",
        foreign_keys="AgentAssignment.assigned_by_user_id",
    )
