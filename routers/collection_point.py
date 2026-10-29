from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models.enums import AccountStatus
from models.user import User
from schemas.collection_point import (
    CollectionPointCreate,
    CollectionPointResponse,
    CollectionPointUpdate,
)
from services.collection_point import CollectionPointService

router = APIRouter(prefix="/collection-points", tags=["Collection points"])


@router.post("/", response_model=CollectionPointResponse, status_code=201)
def create_collection_point(
    payload: CollectionPointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CollectionPointService(db).create(current_user, payload)


@router.get("/", response_model=list[CollectionPointResponse])
def list_collection_points(
    status: AccountStatus | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CollectionPointService(db).list_points(current_user, status)


@router.get("/{point_id}", response_model=CollectionPointResponse)
def get_collection_point(
    point_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CollectionPointService(db).get_point(current_user, point_id)


@router.patch("/{point_id}", response_model=CollectionPointResponse)
def update_collection_point(
    point_id: UUID,
    payload: CollectionPointUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CollectionPointService(db).update(current_user, point_id, payload)


@router.delete("/{point_id}", status_code=204)
def deactivate_collection_point(
    point_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CollectionPointService(db).deactivate(current_user, point_id)
    return Response(status_code=204)
