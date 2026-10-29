from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import DeliveryStatus


class ProduceRecordBase(BaseModel):
    cooperative_id: UUID
    produce_price_id: UUID
    farmer_id: UUID
    device_id: UUID
    collection_point_id: UUID
    delivery_status: DeliveryStatus
    user_id: UUID
    gross_weight_kg: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=3)
    agent_notes: str | None = Field(default=None, max_length=2000)


class ProduceRecordCreate(ProduceRecordBase):
    pass


class ProduceRecordUpdate(BaseModel):
    delivery_status: DeliveryStatus | None = None
    gross_weight_kg: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=10, decimal_places=3)
    agent_notes: str | None = Field(default=None, max_length=2000)


class ProduceRecordResponse(ProduceRecordBase):
    model_config = ConfigDict(from_attributes=True)

    produce_record_id: UUID
    recorded_at: datetime
    amount: Decimal


__all__ = [
    "ProduceRecordBase",
    "ProduceRecordCreate",
    "ProduceRecordResponse",
    "ProduceRecordUpdate",
]
