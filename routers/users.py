from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models.user import User
from schemas.auth import UserResponse as CurrentUserResponse
from schemas.users import (
    AdminCreate,
    AgentCreate,
    AgentRegistrationResponse,
    AgentUpdate,
    FarmerCreate,
    FarmerRegistrationResponse,
    UserResponse,
)
from services.admin_service import AdminService
from services.user_service import UserService

router = APIRouter(prefix="/users")


@router.get("/me", response_model=CurrentUserResponse, tags=["Users"])
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/admins",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def create_admin(
    payload: AdminCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AdminService(db).create_admin(current_user, payload)


@router.post(
    "/agents",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Agents"],
)
def register_agent(
    payload: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).register_agent(current_user, payload)


@router.get("/agents", response_model=list[UserResponse], tags=["Agents"])
def list_agents(
    collection_point_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).list_agents(current_user, collection_point_id)


@router.get("/agents/{agent_id}", response_model=UserResponse, tags=["Agents"])
def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).get_agent(current_user, agent_id)


@router.patch("/agents/{agent_id}", response_model=UserResponse, tags=["Agents"])
def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).update_agent(current_user, agent_id, payload)



@router.post("/agents/{agent_id}/resend-invitation", tags=["Agents"])
def resend_invitation(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).resend_invitation(current_user, agent_id)



@router.post(
    "/farmers",
    response_model=FarmerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Farmers"],
)
def register_farmer(
    payload: FarmerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).register_farmer(current_user, payload)


@router.get("/farmers", response_model=list[UserResponse], tags=["Farmers"])
def list_farmers(
    collection_point_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).list_farmers(current_user, collection_point_id)


@router.get("/farmers/{farmer_id}", response_model=UserResponse, tags=["Farmers"])
def get_farmer(
    farmer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).get_farmer(current_user, farmer_id)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Agents"])
def remove_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserService(db).deactivate_agent(current_user, agent_id)