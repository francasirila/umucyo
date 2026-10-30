from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.produce_price import ProducePrice
from repositories.produce_price import ProducePriceRepository
from schemas.produce_price import ProducePriceCreate, ProducePriceUpdate


class ProducePriceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProducePriceRepository(db)

    def get_produce_price(self, produce_price_id: UUID) -> ProducePrice:
        price = self.repository.get_by_id(produce_price_id)

        if price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produce price not found",
            )

        return price

    def list_produce_prices(
        self,
        *,
        cooperative_id: UUID | None = None,
        unit: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProducePrice]:
        return self.repository.list(
            cooperative_id=cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
            skip=skip,
            limit=limit,
        )

    def count_produce_prices(
        self,
        *,
        cooperative_id: UUID | None = None,
        unit: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
    ) -> int:
        return self.repository.count(
            cooperative_id=cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
        )

    def create_produce_price(
        self,
        payload: ProducePriceCreate,
    ) -> ProducePrice:
        data = payload.model_dump()

        self._require(
            Cooperative,
            data["cooperative_id"],
            "Cooperative",
        )

        creator = self._require(
            CooperativeUser,
            data["created_by_user_id"],
            "Cooperative user",
        )

        if creator.cooperative_id != data["cooperative_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user must belong to the specified cooperative",
            )

        self._validate_period(
            data["effective_from"],
            data.get("effective_to"),
        )

        self._ensure_no_overlap(
            cooperative_id=data["cooperative_id"],
            unit=data["unit"],
            effective_from=data["effective_from"],
            effective_to=data.get("effective_to"),
        )

        return self.repository.create(data)

    def update_produce_price(
        self,
        produce_price_id: UUID,
        payload: ProducePriceUpdate,
    ) -> ProducePrice:
        price = self.get_produce_price(produce_price_id)
        data = payload.model_dump(exclude_unset=True)

        effective_from = data.get("effective_from", price.effective_from)
        effective_to = data.get("effective_to", price.effective_to)
        unit = data.get("unit", price.unit)

        self._validate_period(effective_from, effective_to)

        self._ensure_no_overlap(
            cooperative_id=price.cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
            exclude_price_id=produce_price_id,
        )

        return self.repository.update(price, data)

    def deactivate_produce_price(
        self,
        produce_price_id: UUID,
    ) -> ProducePrice:
        price = self.get_produce_price(produce_price_id)

        now = datetime.now(timezone.utc)
        effective_from = price.effective_from
        if effective_from.tzinfo is None:
            effective_from = effective_from.replace(tzinfo=timezone.utc)

        if effective_from >= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A price cannot be deactivated before its effective period begins",
            )

        if price.effective_to is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produce price is inactive",
            )

        return self.repository.update(price, {"effective_to": now})

    def delete_produce_price(self, produce_price_id: UUID) -> None:
        price = self.get_produce_price(produce_price_id)
        self.repository.delete(price)

    def _require(self, model, entity_id: UUID, label: str):
        entity = self.db.get(model, entity_id)

        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{label} not found",
            )

        return entity

    def _validate_period(
        self,
        effective_from: datetime,
        effective_to: datetime | None,
    ) -> None:
        if effective_to is not None and effective_to <= effective_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="effective_to must be later than effective_from",
            )

    def _ensure_no_overlap(
        self,
        *,
        cooperative_id: UUID,
        unit: str,
        effective_from: datetime,
        effective_to: datetime | None,
        exclude_price_id: UUID | None = None,
    ) -> None:
        overlapping_price = self.repository.find_overlapping(
            cooperative_id=cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
            exclude_price_id=exclude_price_id,
        )

        if overlapping_price is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The effective period overlaps an existing price for this cooperative and unit",
            )


__all__ = ["ProducePriceService"]
