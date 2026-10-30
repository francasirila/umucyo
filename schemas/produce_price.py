from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProducePriceBase(BaseModel):
    cooperative_id: UUID
    unit: str = Field(default="kg", max_length=20)
    price_per_unit: Decimal = Field(
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    effective_from: datetime
    effective_to: datetime | None = None
    created_by_user_id: UUID


class ProducePriceCreate(ProducePriceBase):
    pass


class ProducePriceUpdate(BaseModel):
    unit: str | None = Field(default=None, max_length=20)
    price_per_unit: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class ProducePriceResponse(ProducePriceBase):
    model_config = ConfigDict(from_attributes=True)
    produce_price_id: UUID
    created_at: datetime


__all__ = [
    "ProducePriceBase",
    "ProducePriceCreate",
    "ProducePriceResponse",
    "ProducePriceUpdate",
]
