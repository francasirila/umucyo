from fastapi import Depends, HTTPException

from core.security import get_current_user
from models.enums import UserRole
from models.user import User


def require_active_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_admin(user: User = Depends(require_active_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user


def require_agent(user: User = Depends(require_active_user)) -> User:
    if user.role != UserRole.agent:
        raise HTTPException(status_code=403, detail="Agent access required.")
    return user


def require_staff(user: User = Depends(require_active_user)) -> User:
    if user.role not in {UserRole.admin, UserRole.agent}:
        raise HTTPException(status_code=403, detail="Staff access required.")
    return user
