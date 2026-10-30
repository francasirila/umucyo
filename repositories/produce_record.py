from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.enums import DeliveryStatus
from models.produce_record import ProduceRecord


class ProduceRecordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, produce_record_id: UUID) -> ProduceRecord | None:
        return self.db.get(ProduceRecord, produce_record_id)

    def list(
        self,
        *,
        cooperative_id: UUID | None = None,
        farmer_id: UUID | None = None,
        collection_point_id: UUID | None = None,
        device_id: UUID | None = None,
        delivery_status: DeliveryStatus | None = None,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProduceRecord]:
        stmt = self._filtered_query(
            cooperative_id=cooperative_id,
            farmer_id=farmer_id,
            collection_point_id=collection_point_id,
            device_id=device_id,
            delivery_status=delivery_status,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )
        stmt = stmt.order_by(ProduceRecord.recorded_at.desc(), ProduceRecord.produce_record_id)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(
        self,
        *,
        cooperative_id: UUID | None = None,
        farmer_id: UUID | None = None,
        collection_point_id: UUID | None = None,
        device_id: UUID | None = None,
        delivery_status: DeliveryStatus | None = None,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
    ) -> int:
        stmt = self._filtered_query(
            cooperative_id=cooperative_id,
            farmer_id=farmer_id,
            collection_point_id=collection_point_id,
            device_id=device_id,
            delivery_status=delivery_status,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return self.db.scalar(count_stmt) or 0

    def create(self, data: dict) -> ProduceRecord:
        record = ProduceRecord(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, record: ProduceRecord, data: dict) -> ProduceRecord:
        for field, value in data.items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, record: ProduceRecord) -> None:
        self.db.delete(record)
        self.db.commit()

    def _filtered_query(
        self,
        *,
        cooperative_id: UUID | None,
        farmer_id: UUID | None,
        collection_point_id: UUID | None,
        device_id: UUID | None,
        delivery_status: DeliveryStatus | None,
        recorded_from: datetime | None,
        recorded_to: datetime | None,
    ) -> Select:
        stmt = select(ProduceRecord)
        if cooperative_id is not None:
            stmt = stmt.where(ProduceRecord.cooperative_id == cooperative_id)
        if farmer_id is not None:
            stmt = stmt.where(ProduceRecord.farmer_id == farmer_id)
        if collection_point_id is not None:
            stmt = stmt.where(ProduceRecord.collection_point_id == collection_point_id)
        if device_id is not None:
            stmt = stmt.where(ProduceRecord.device_id == device_id)
        if delivery_status is not None:
            stmt = stmt.where(ProduceRecord.delivery_status == delivery_status)
        if recorded_from is not None:
            stmt = stmt.where(ProduceRecord.recorded_at >= recorded_from)
        if recorded_to is not None:
            stmt = stmt.where(ProduceRecord.recorded_at <= recorded_to)
        return stmt


__all__ = ["ProduceRecordRepository"]
