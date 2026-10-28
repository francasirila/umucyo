from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import DeliveryStatus


class ProduceRecordBase(BaseModel):
    cooperative_id: UUID = Field(description="Cooperative receiving the produce delivery")
    produce_price_id: UUID = Field(description="Produce price applied to the delivery")
    farmer_id: UUID = Field(description="Farmer delivering the produce")
    device_id: UUID = Field(description="Weighing device used to capture the weight")
    collection_point_id: UUID = Field(description="Collection point where the delivery was recorded")
    delivery_status: DeliveryStatus = Field(description="Outcome of the delivery")
    user_id: UUID = Field(description="Cooperative agent recording the delivery")
    gross_weight_kg: Decimal = Field(
        gt=Decimal("0"),
        max_digits=10,
        decimal_places=3,
        description="Weight measured by the device, in kilograms",
    )
    agent_notes: str | None = Field(default=None, max_length=2000, description="Optional notes from the agent")


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
    amount: Decimal = Field(description="Amount owed to the farmer, calculated by the backend")


__all__ = [
    "ProduceRecordBase",
    "ProduceRecordCreate",
    "ProduceRecordResponse",
    "ProduceRecordUpdate",
]
