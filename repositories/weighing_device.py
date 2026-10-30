from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.enums import AccountStatus
from models.weighing_device import WeighingDevice


class WeighingDeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, device_id: UUID) -> WeighingDevice | None:
        return self.db.get(WeighingDevice, device_id)

    def get_by_serial_number(self, serial_number: str) -> WeighingDevice | None:
        stmt = select(WeighingDevice).where(WeighingDevice.serial_number == serial_number)
        return self.db.scalar(stmt)

    def get_all(
        self,
        collection_point_id: UUID | None = None,
        status: AccountStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WeighingDevice]:
        stmt = select(WeighingDevice)
        if collection_point_id is not None:
            stmt = stmt.where(WeighingDevice.collection_point_id == collection_point_id)
        if status is not None:
            stmt = stmt.where(WeighingDevice.status == status)
        stmt = stmt.order_by(WeighingDevice.registered_at.desc(), WeighingDevice.device_id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(WeighingDevice)) or 0

    def create(self, device: WeighingDevice) -> WeighingDevice:
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def update(self, device: WeighingDevice) -> WeighingDevice:
        self.db.commit()
        self.db.refresh(device)
        return device

    def delete(self, device: WeighingDevice) -> None:
        self.db.delete(device)
        self.db.commit()
