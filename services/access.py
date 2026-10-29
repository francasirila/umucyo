from uuid import UUID

from sqlalchemy.orm import Session
from core.exceptions import ServiceError
from core.utils import enum_value
from models.collection_point import CollectionPoint
from models.enums import AccountStatus, UserRole


def role_of(user) -> str:
    return str(enum_value(user.role))


def cooperative_id_of(user) -> UUID | None:
    return getattr(user, "cooperative_id", None)


def require_admin(user) -> UUID:
    cooperative_id = cooperative_id_of(user)
    if role_of(user) != UserRole.admin.value or not cooperative_id:
        raise ServiceError(403, "Administrator access is required.")
    return cooperative_id


def require_staff(user) -> UUID:
    if role_of(user) not in {UserRole.admin.value, UserRole.agent.value}:
        raise ServiceError(403, "Cooperative staff access is required.")

    cooperative_id = cooperative_id_of(user)
    if not cooperative_id:
        raise ServiceError(403, "You are not associated with a cooperative.")
    return cooperative_id


def get_active_point(db: Session, user, point_id: UUID) -> CollectionPoint:
    point = db.get(CollectionPoint, point_id)

    if point is None or point.cooperative_id != cooperative_id_of(user):
        raise ServiceError(404, "Collection point not found in your cooperative.")

    if role_of(user) == UserRole.agent.value:
        if getattr(user, "collection_point_id", None) != point_id:
            raise ServiceError(403, "You are not assigned to this collection point.")

    if point.status != AccountStatus.active:
        raise ServiceError(409, "The collection point is inactive.")

    return point
