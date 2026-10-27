import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "task"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=True,
    )
    message_id = Column(UUID(as_uuid=True), ForeignKey("message_log.message_id"), nullable=True)
    description = Column(String(1000), nullable=False)
    priority = Column(
        Enum(TaskPriority, name="task_priority"),
        nullable=False,
        default=TaskPriority.NORMAL,
    )
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.OPEN)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    created_by = relationship("User", back_populates="created_tasks", foreign_keys=[created_by_user_id])
    assigned_to = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to_user_id])
    collection_point = relationship("CollectionPoint", back_populates="tasks")
    message = relationship("MessageLog", back_populates="tasks")
