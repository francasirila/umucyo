from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from models.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    cooperative_id: UUID
    created_by_user_id: UUID
    assigned_to_user_id: UUID
    collection_point_id: UUID | None = None
    description: str = Field(min_length=1)
    priority: TaskPriority = TaskPriority.normal


class TaskUpdate(BaseModel):
    assigned_to_user_id: UUID | None = None
    collection_point_id: UUID | None = None
    description: str | None = Field(default=None, min_length=1)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    cooperative_id: UUID
    created_by_user_id: UUID
    assigned_to_user_id: UUID
    collection_point_id: UUID | None
    description: str
    priority: TaskPriority
    created_at: datetime
    status: TaskStatus
    completed_at: datetime | None
