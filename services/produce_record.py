from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.enums import AccountStatus, DeliveryStatus
from models.farmer import Farmer
from models.produce_price import ProducePrice
from models.produce_record import ProduceRecord
from models.weighing_device import WeighingDevice
from repositories.produce_record import ProduceRecordRepository
from schemas.produce_record import ProduceRecordCreate, ProduceRecordUpdate


class ProduceRecordService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProduceRecordRepository(db)

    def get_produce_record(self, produce_record_id: UUID) -> ProduceRecord:
        record = self.repository.get_by_id(produce_record_id)
        if record is None:
            raise HTTPException(404, f"Produce record {produce_record_id} not found")
        return record

    def list_produce_records(self, **filters) -> list[ProduceRecord]:
        return self.repository.list(**filters)

    def create_produce_record(self, payload: ProduceRecordCreate) -> ProduceRecord:
        cooperative = self._require(Cooperative, payload.cooperative_id, "Cooperative")
        produce_price = self._require(ProducePrice, payload.produce_price_id, "Produce price")
        farmer = self._require_farmer(payload.farmer_id)
        device = self._require(WeighingDevice, payload.device_id, "Weighing device")
        collection_point = self._require(CollectionPoint, payload.collection_point_id, "Collection point")
        agent = self._require(CooperativeUser, payload.user_id, "Cooperative user")

        self._ensure(
            produce_price.cooperative_id == cooperative.cooperative_id, "Produce price does not belong to the given cooperative"
        )
        self._ensure(
            collection_point.cooperative_id == cooperative.cooperative_id,
            "Collection point does not belong to the given cooperative",
        )
        self._ensure(
            device.collection_point_id == collection_point.collection_point_id,
            "Weighing device is not registered at the given collection point",
        )
        self._ensure(
            farmer.collection_point_id == collection_point.collection_point_id,
            "Farmer is not registered at the given collection point",
        )
        self._ensure(agent.cooperative_id == cooperative.cooperative_id, "Agent does not belong to the given cooperative")
        self._ensure(device.status == AccountStatus.active, "Weighing device is not active")
        self._ensure(collection_point.status == AccountStatus.active, "Collection point is not active")

        data = payload.model_dump()
        data["amount"] = self._calculate_amount(payload.delivery_status, payload.gross_weight_kg, produce_price)
        return self.repository.create(data)

    def update_produce_record(self, produce_record_id: UUID, payload: ProduceRecordUpdate) -> ProduceRecord:
        record = self.get_produce_record(produce_record_id)
        changes = payload.model_dump(exclude_unset=True)

        if "delivery_status" in changes or "gross_weight_kg" in changes:
            produce_price = self._require(ProducePrice, record.produce_price_id, "Produce price")
            changes["amount"] = self._calculate_amount(
                changes.get("delivery_status", record.delivery_status),
                changes.get("gross_weight_kg", record.gross_weight_kg),
                produce_price,
            )

        return self.repository.update(record, changes)

    def delete_produce_record(self, produce_record_id: UUID) -> None:
        self.repository.delete(self.get_produce_record(produce_record_id))

    def _calculate_amount(
        self, delivery_status: DeliveryStatus, gross_weight_kg: Decimal, produce_price: ProducePrice
    ) -> Decimal:
        if delivery_status == DeliveryStatus.rejected:
            return Decimal("0")
        return (gross_weight_kg * produce_price.price_per_unit).quantize(Decimal("0.01"))

    def _require(self, model, entity_id: UUID, label: str):
        entity = self.db.get(model, entity_id)
        if entity is None:
            raise HTTPException(404, f"{label} {entity_id} not found")
        return entity

    def _require_farmer(self, farmer_id: UUID) -> Farmer:
        farmer = self.db.query(Farmer).filter(Farmer.user_id == farmer_id).first()
        if farmer is None:
            raise HTTPException(404, f"Farmer {farmer_id} not found")
        return farmer

    @staticmethod
    def _ensure(condition: bool, detail: str) -> None:
        if not condition:
            raise HTTPException(422, detail)


__all__ = ["ProduceRecordService"]
