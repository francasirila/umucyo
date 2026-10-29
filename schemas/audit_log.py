from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    audit_log_id: UUID
    user_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID
    old_values: Any | None = None
    new_values: Any | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
