from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from models.enums import AccountStatus, UserRole


class CooperativeRegistration(BaseModel):
    cooperative_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)



class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOTPRequest(BaseModel):
    email: EmailStr


class SetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8, max_length=128)


class BootstrapAdminRequest(CooperativeRegistration):
    pass


class UserResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    role: UserRole
    status: AccountStatus
    email: EmailStr | None = None
    phone_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CooperativeRegistrationResponse(BaseModel):
    message: str
    admin: UserResponse


class LoginResponse(BaseModel):
    requires_otp: bool
    message: str
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
