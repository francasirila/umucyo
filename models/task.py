import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base
from models.enums import TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "task"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=True)
    description = Column(Text, nullable=False)
    priority = Column(Enum(TaskPriority, name="task_priority"), nullable=False, default=TaskPriority.normal)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.open)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    cooperative = relationship("Cooperative", back_populates="tasks")
    created_by = relationship("CooperativeUser", foreign_keys=[created_by_user_id], back_populates="created_tasks")
    assigned_to = relationship("CooperativeUser", foreign_keys=[assigned_to_user_id], back_populates="assigned_tasks")
    collection_point = relationship("CollectionPoint", back_populates="tasks")
