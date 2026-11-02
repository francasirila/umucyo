from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from core.rate_limit import limiter
from core.security import get_current_user
from database import get_db
from models.user import User
from schemas.auth import (
    CooperativeRegistration,
    CooperativeRegistrationResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResendOTPRequest,
    SetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyOTPRequest,
)
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/cooperative", response_model=CooperativeRegistrationResponse, status_code=201)
@limiter.limit("5/15minutes")
def register_cooperative(payload: CooperativeRegistration, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).register_cooperative(payload)


@router.post("/bootstrap-admin", response_model=CooperativeRegistrationResponse, status_code=201)
@limiter.limit("5/15minutes")
def bootstrap_admin(
    payload: CooperativeRegistration,
    request: Request,
    x_bootstrap_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    return AuthService(db).bootstrap_admin(payload, x_bootstrap_key)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/5minutes")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).login(str(payload.email), payload.password)


@router.post("/resend-otp", response_model=LoginResponse)
@limiter.limit("5/15minutes")
def resend_otp(payload: ResendOTPRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).resend_login_otp(str(payload.email))


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit("10/15minutes")
def verify_otp(payload: VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).verify_login_otp(str(payload.email), payload.code)


@router.post("/set-password", response_model=MessageResponse)
@limiter.limit("5/15minutes")
def set_password(payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).set_password(payload.token, payload.password)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AuthService(db).logout(current_user)
