from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.enums import AccountStatus
from schemas.weighing_device import WeighingDeviceCreate, WeighingDeviceResponse, WeighingDeviceUpdate
from services.weighing_device import WeighingDeviceService

router = APIRouter(prefix="/weighing-devices", tags=["Weighing Devices"])


def get_weighing_device_service(db: Session = Depends(get_db)) -> WeighingDeviceService:
    return WeighingDeviceService(db)


@router.post("", response_model=WeighingDeviceResponse, status_code=status.HTTP_201_CREATED, summary="Register a weighing device")
def register_weighing_device(
    payload: WeighingDeviceCreate,
    service: WeighingDeviceService = Depends(get_weighing_device_service),
):
    return service.create_device(payload)


@router.get("", response_model=list[WeighingDeviceResponse], summary="List weighing devices")
def list_weighing_devices(
    collection_point_id: UUID | None = None,
    device_status: AccountStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    service: WeighingDeviceService = Depends(get_weighing_device_service),
):
    return service.list_devices(
        collection_point_id=collection_point_id,
        device_status=device_status,
        skip=skip,
        limit=limit,
    )


@router.get("/{device_id}", response_model=WeighingDeviceResponse, summary="Get a weighing device")
def get_weighing_device(
    device_id: UUID,
    service: WeighingDeviceService = Depends(get_weighing_device_service),
):
    return service.get_device(device_id)


@router.patch("/{device_id}", response_model=WeighingDeviceResponse, summary="Update a weighing device")
def update_weighing_device(
    device_id: UUID,
    payload: WeighingDeviceUpdate,
    service: WeighingDeviceService = Depends(get_weighing_device_service),
):
    return service.update_device(device_id, payload)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a weighing device")
def delete_weighing_device(
    device_id: UUID,
    service: WeighingDeviceService = Depends(get_weighing_device_service),
):
    service.delete_device(device_id)
