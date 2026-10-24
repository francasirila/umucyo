import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import AccountStatus, UserRole


class User(Base):
    __tablename__ = "user"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status = Column(
        Enum(AccountStatus, name="account_status"),
        nullable=False,
        default=AccountStatus.active,
        server_default="active",
    )

    cooperative = relationship("Cooperative", back_populates="users")

    agent_assignments = relationship(
        "AgentAssignment",
        back_populates="user",
        foreign_keys="AgentAssignment.user_id",
    )

    assignments_created = relationship(
        "AgentAssignment",
        back_populates="assigned_by",
        foreign_keys="AgentAssignment.assigned_by_user_id",
    )

    tasks_assigned = relationship(
        "Task",
        back_populates="assigned_user",
        foreign_keys="Task.assigned_to_user_id",
    )

    tasks_created = relationship(
        "Task",
        back_populates="created_by",
        foreign_keys="Task.created_by_user_id",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.user_id",
    )
