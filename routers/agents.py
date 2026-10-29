from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models.user import User
from schemas.users import AgentCreate, AgentRegistrationResponse, AgentUpdate, UserResponse
from services.agent_service import AgentService

router = APIRouter(prefix="/users/agents", tags=["Agents"])


@router.post("", response_model=AgentRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_agent(
    payload: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AgentService(db).register_agent(current_user, payload)


@router.patch("/{agent_id}", response_model=UserResponse)
def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AgentService(db).update_agent(current_user, agent_id, payload)


@router.get("", response_model=list[UserResponse])
def list_agents(
    collection_point_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AgentService(db).list_agents(current_user, collection_point_id)


@router.get("/{agent_id}", response_model=UserResponse)
def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AgentService(db).get_agent(current_user, agent_id)
