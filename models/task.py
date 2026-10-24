import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "task"
    __table_args__ = (
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name="ck_task_completed_at",
        ),
    )

    task_id = Column(
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

    farmer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("farmer.farmer_id"),
        nullable=True,
        index=True,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False
    )
    assigned_to_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False, index=True
    )
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("message_log.message_id"),
        nullable=True,
        index=True,
    )
    description = Column(Text, nullable=False)
    priority = Column(
        Enum(TaskPriority, name="task_priority"),
        nullable=False,
        default=TaskPriority.normal,
        server_default="normal",
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status = Column(
        Enum(TaskStatus, name="task_status"),
        nullable=False,
        default=TaskStatus.open,
        server_default="open",
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    cooperative = relationship(
        "Cooperative",
        back_populates="tasks",
    )

    farmer = relationship(
        "Farmer",
        back_populates="tasks",
    )

    collection_point = relationship(
        "CollectionPoint",
        back_populates="tasks",
    )

    assigned_user = relationship(
        "User",
        back_populates="tasks_assigned",
        foreign_keys=[assigned_to_user_id],
    )

    created_by = relationship(
        "User",
        back_populates="tasks_created",
        foreign_keys=[created_by_user_id],
    )
