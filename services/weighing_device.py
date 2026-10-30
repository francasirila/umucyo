from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.collection_point import CollectionPoint
from models.enums import AccountStatus
from models.weighing_device import WeighingDevice
from repositories.weighing_device import WeighingDeviceRepository
from schemas.weighing_device import WeighingDeviceCreate, WeighingDeviceUpdate


class WeighingDeviceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = WeighingDeviceRepository(db)

    def create_device(self, payload: WeighingDeviceCreate) -> WeighingDevice:
        collection_point = self.db.get(CollectionPoint, payload.collection_point_id)
        if collection_point is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection point not found")

        if self.repository.get_by_serial_number(payload.serial_number) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A weighing device with serial number '{payload.serial_number}' already exists",
            )

        device = WeighingDevice(
            collection_point_id=payload.collection_point_id,
            serial_number=payload.serial_number,
            status=payload.status,
        )
        return self.repository.create(device)

    def get_device(self, device_id: UUID) -> WeighingDevice:
        device = self.repository.get_by_id(device_id)
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weighing device not found")
        return device

    def list_devices(
        self,
        collection_point_id: UUID | None = None,
        device_status: AccountStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WeighingDevice]:
        return self.repository.get_all(
            collection_point_id=collection_point_id,
            status=device_status,
            skip=skip,
            limit=limit,
        )

    def update_device(self, device_id: UUID, payload: WeighingDeviceUpdate) -> WeighingDevice:
        device = self.get_device(device_id)

        if payload.serial_number is not None and payload.serial_number != device.serial_number:
            if self.repository.get_by_serial_number(payload.serial_number) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A weighing device with serial number '{payload.serial_number}' already exists",
                )
            device.serial_number = payload.serial_number

        if payload.status is not None:
            device.status = payload.status

        return self.repository.update(device)

    def delete_device(self, device_id: UUID) -> None:
        device = self.get_device(device_id)
        self.repository.delete(device)
