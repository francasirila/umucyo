from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from core.security import get_current_user
from database import get_db
from models.user import User
from schemas.users import FarmerCreate, FarmerRegistrationResponse, UserResponse
from services.farmer_service import FarmerService

router = APIRouter(prefix="/users/farmers", tags=["Farmers"])


@router.post("", response_model=FarmerRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_farmer(
    payload: FarmerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FarmerService(db).register_farmer(current_user, payload)


@router.get("", response_model=list[UserResponse])
def list_farmers(
    collection_point_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FarmerService(db).list_farmers(current_user, collection_point_id)


@router.get("/{farmer_id}", response_model=UserResponse)
def get_farmer(
    farmer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FarmerService(db).get_farmer(current_user, farmer_id)
