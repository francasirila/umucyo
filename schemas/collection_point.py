from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import AccountStatus


class CollectionPointCreate(BaseModel):
    collection_name: str = Field(min_length=2, max_length=100)


class CollectionPointUpdate(BaseModel):
    collection_name: str | None = Field(default=None, min_length=2, max_length=100)
    status: AccountStatus | None = None


class CollectionPointResponse(BaseModel):
    collection_point_id: UUID
    cooperative_id: UUID
    collection_name: str
    status: AccountStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
