"""HTTP endpoints for the produce_record resource."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.enums import DeliveryStatus
from schemas.produce_record import ProduceRecordCreate, ProduceRecordResponse, ProduceRecordUpdate
from services.produce_record import ProduceRecordService

router = APIRouter(prefix="/produce-records", tags=["Produce Records"])


def get_produce_record_service(db: Session = Depends(get_db)) -> ProduceRecordService:
    return ProduceRecordService(db)


@router.post("", response_model=ProduceRecordResponse, status_code=status.HTTP_201_CREATED, summary="Record a produce delivery")
def create_produce_record(
    payload: ProduceRecordCreate,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.create_produce_record(payload)


@router.get("", response_model=list[ProduceRecordResponse], summary="List produce records")
def list_produce_records(
    cooperative_id: UUID | None = Query(default=None, description="Filter by cooperative"),
    farmer_id: UUID | None = Query(default=None, description="Filter by farmer"),
    collection_point_id: UUID | None = Query(default=None, description="Filter by collection point"),
    device_id: UUID | None = Query(default=None, description="Filter by weighing device"),
    delivery_status: DeliveryStatus | None = Query(default=None, description="Filter by delivery status"),
    recorded_from: datetime | None = Query(default=None, description="Only records recorded at or after this time"),
    recorded_to: datetime | None = Query(default=None, description="Only records recorded at or before this time"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records to return"),
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


@router.get("/{produce_record_id}", response_model=ProduceRecordResponse, summary="Get a produce record")
def get_produce_record(
    produce_record_id: UUID,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.get_produce_record(produce_record_id)


@router.patch("/{produce_record_id}", response_model=ProduceRecordResponse, summary="Update a produce record")
def update_produce_record(
    produce_record_id: UUID,
    payload: ProduceRecordUpdate,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> ProduceRecordResponse:
    return service.update_produce_record(produce_record_id, payload)


@router.delete("/{produce_record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a produce record")
def delete_produce_record(
    produce_record_id: UUID,
    service: ProduceRecordService = Depends(get_produce_record_service),
) -> None:
    service.delete_produce_record(produce_record_id)


__all__ = ["router"]
