"""HTTP endpoints for the produce_record resource."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.enums import DeliveryStatus
from schemas.produce_record import ProduceRecordCreate, ProduceRecordResponse, ProduceRecordUpdate
from services.produce_record import ProduceRecordService

router = APIRouter(prefix="/produce-records", tags=["Produce Records"])


def get_produce_record_service(db: Session = Depends(get_db)) -> ProduceRecordService:
    return ProduceRecordService(db)


@router.post("", response_model=ProduceRecordResponse, status_code=status.HTTP_201_CREATED)
def create_produce_record(
    payload: ProduceRecordCreate,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.create_produce_record(payload)


@router.get("", response_model=list[ProduceRecordResponse])
def list_produce_records(
    cooperative_id: UUID | None = None,
    farmer_id: UUID | None = None,
    collection_point_id: UUID | None = None,
    device_id: UUID | None = None,
    delivery_status: DeliveryStatus | None = None,
    recorded_from: datetime | None = None,
    recorded_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> list[ProduceRecordResponse]:
    return service.list_produce_records(
        cooperative_id=cooperative_id,
        farmer_id=farmer_id,
        collection_point_id=collection_point_id,
        device_id=device_id,
        delivery_status=delivery_status,
        recorded_from=recorded_from,
        recorded_to=recorded_to,
        skip=skip,
        limit=limit,
    )


@router.get("/{produce_record_id}", response_model=ProduceRecordResponse)
def get_produce_record(
    produce_record_id: UUID,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.get_produce_record(produce_record_id)


@router.patch("/{produce_record_id}", response_model=ProduceRecordResponse)
def update_produce_record(
    produce_record_id: UUID,
    payload: ProduceRecordUpdate,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.update_produce_record(produce_record_id, payload)


@router.delete("/{produce_record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produce_record(
    produce_record_id: UUID,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> None:
    service.delete_produce_record(produce_record_id)


__all__ = ["router"]
