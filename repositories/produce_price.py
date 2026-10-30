from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.produce_price import ProducePrice


class ProducePriceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, produce_price_id: UUID) -> ProducePrice | None:
        return self.db.get(ProducePrice, produce_price_id)

    def list(
        self,
        *,
        cooperative_id: UUID | None = None,
        unit: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProducePrice]:
        stmt = self._filtered_query(
            cooperative_id=cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        stmt = stmt.order_by(
            ProducePrice.effective_from.desc(),
            ProducePrice.produce_price_id,
        )
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(
        self,
        *,
        cooperative_id: UUID | None = None,
        unit: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
    ) -> int:
        stmt = self._filtered_query(
            cooperative_id=cooperative_id,
            unit=unit,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return self.db.scalar(count_stmt) or 0

    def find_overlapping(
        self,
        *,
        cooperative_id: UUID,
        unit: str,
        effective_from: datetime,
        effective_to: datetime | None,
        exclude_price_id: UUID | None = None,
    ) -> ProducePrice | None:
        stmt = select(ProducePrice).where(
            ProducePrice.cooperative_id == cooperative_id,
            ProducePrice.unit == unit,
        )

        if effective_to is not None:
            stmt = stmt.where(ProducePrice.effective_from < effective_to)

        stmt = stmt.where((ProducePrice.effective_to.is_(None)) | (ProducePrice.effective_to > effective_from))

        if exclude_price_id is not None:
            stmt = stmt.where(ProducePrice.produce_price_id != exclude_price_id)

        return self.db.scalars(stmt.limit(1)).first()

    def create(self, data: dict) -> ProducePrice:
        price = ProducePrice(**data)
        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)
        return price

    def update(self, price: ProducePrice, data: dict) -> ProducePrice:
        for field, value in data.items():
            setattr(price, field, value)
        self.db.commit()
        self.db.refresh(price)
        return price

    def delete(self, price: ProducePrice) -> None:
        self.db.delete(price)
        self.db.commit()

    def _filtered_query(
        self,
        *,
        cooperative_id: UUID | None,
        unit: str | None,
        effective_from: datetime | None,
        effective_to: datetime | None,
    ) -> Select:
        stmt = select(ProducePrice)

        if cooperative_id is not None:
            stmt = stmt.where(ProducePrice.cooperative_id == cooperative_id)

        if unit is not None:
            stmt = stmt.where(ProducePrice.unit == unit)

        if effective_from is not None:
            stmt = stmt.where(ProducePrice.effective_from >= effective_from)

        if effective_to is not None:
            stmt = stmt.where(ProducePrice.effective_from <= effective_to)
        return stmt


__all__ = ["ProducePriceRepository"]
