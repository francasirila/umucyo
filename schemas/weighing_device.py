from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import AccountStatus


class WeighingDeviceCreate(BaseModel):
    collection_point_id: UUID
    serial_number: str = Field(min_length=1, max_length=100)
    status: AccountStatus = AccountStatus.active


class WeighingDeviceUpdate(BaseModel):
    serial_number: str | None = Field(default=None, min_length=1, max_length=100)
    status: AccountStatus | None = None


class WeighingDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: UUID
    collection_point_id: UUID
    serial_number: str
    status: AccountStatus
    registered_at: datetime
