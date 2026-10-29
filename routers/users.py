from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models.user import User
from schemas.auth import UserResponse as CurrentUserResponse
from schemas.users import AdminCreate, UserResponse
from services.admin_service import AdminService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AdminService(db).create_admin(current_user, payload)
