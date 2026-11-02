from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.enums import AccountStatus, UserRole


PHONE_PATTERN = r"^\+[1-9]\d{7,14}$"


class UserResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    role: UserRole
    status: AccountStatus
    email: EmailStr | None = None
    phone_number: str | None = None
    collection_point_id: UUID | None = None
    registered_by_user_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(UserResponse):
    assigned_collection_point_id: UUID | None = None
    collection_point_name: str | None = None


class AgentCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    collection_name: str = Field(min_length=1, max_length=100)


class FarmerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(pattern=PHONE_PATTERN)
    collection_point_id: UUID


class FarmerUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    phone_number: str | None = Field(
        default=None,
        pattern=PHONE_PATTERN,
    )

    collection_point_id: UUID | None = None
    status: AccountStatus | None = None


class AgentUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    status: AccountStatus | None = None


class AgentRegistrationResponse(BaseModel):
    message: str
    agent: UserResponse
    invitation_sent: bool


class FarmerRegistrationResponse(BaseModel):
    message: str
    farmer: UserResponse
    sms_sent: bool


class AdminCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class CooperativeProfileUpdate(BaseModel):
    cooperative_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )


class CooperativeProfileResponse(BaseModel):
    cooperative_id: UUID
    cooperative_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)



class SetPasswordRequest(BaseModel):
    token: str
    password: str