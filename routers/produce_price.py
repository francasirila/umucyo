from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.produce_price import (
    ProducePriceCreate,
    ProducePriceResponse,
    ProducePriceUpdate,
)
from services.produce_price import ProducePriceService


router = APIRouter(prefix="/tea-prices", tags=["Tea Prices"])


def get_produce_price_service(
    db: Session = Depends(get_db),
) -> ProducePriceService:
    return ProducePriceService(db)


@router.post(
    "",
    response_model=ProducePriceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_produce_price(
    payload: ProducePriceCreate,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> ProducePriceResponse:
    return service.create_produce_price(payload)


@router.get("", response_model=list[ProducePriceResponse])
def list_produce_prices(
    cooperative_id: UUID | None = None,
    unit: str | None = None,
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> list[ProducePriceResponse]:
    return service.list_produce_prices(
        cooperative_id=cooperative_id,
        unit=unit,
        effective_from=effective_from,
        effective_to=effective_to,
        skip=skip,
        limit=limit,
    )


@router.get("/{produce_price_id}", response_model=ProducePriceResponse)
def get_produce_price(
    produce_price_id: UUID,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> ProducePriceResponse:
    return service.get_produce_price(produce_price_id)


@router.patch("/{produce_price_id}", response_model=ProducePriceResponse)
def update_produce_price(
    produce_price_id: UUID,
    payload: ProducePriceUpdate,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> ProducePriceResponse:
    return service.update_produce_price(produce_price_id, payload)


@router.post(
    "/{produce_price_id}/deactivate",
    response_model=ProducePriceResponse,
)
def deactivate_produce_price(
    produce_price_id: UUID,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> ProducePriceResponse:
    return service.deactivate_produce_price(produce_price_id)


@router.delete(
    "/{produce_price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_produce_price(
    produce_price_id: UUID,
    service: ProducePriceService = Depends(get_produce_price_service),
) -> None:
    service.delete_produce_price(produce_price_id)


__all__ = ["router"]
