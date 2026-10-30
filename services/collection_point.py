from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.exceptions import ServiceError
from core.utils import enum_value
from models.collection_point import CollectionPoint
from models.enums import AccountStatus, UserRole
from services.access import require_admin, require_staff, role_of
from services.audit_service import AuditService

NAME_TOO_SHORT = "Collection point name must contain at least two non-space characters."
NAME_EXISTS = "A collection point with this name already exists in this cooperative."


def commit_session(db):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


class CollectionPointService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def _get_owned_point(self, user, point_id: UUID) -> CollectionPoint:
        cooperative_id = require_staff(user)

        point = self.db.scalar(
            select(CollectionPoint).where(
                CollectionPoint.collection_point_id == point_id,
                CollectionPoint.cooperative_id == cooperative_id,
            )
        )

        if point is None:
            raise ServiceError(404, "Collection point not found.")

        if role_of(user) == UserRole.agent.value and user.collection_point_id != point.collection_point_id:
            raise ServiceError(404, "Collection point not found.")

        return point

    def _name_exists(self, cooperative_id, name: str, exclude_id=None) -> bool:
        query = select(CollectionPoint.collection_point_id).where(
            CollectionPoint.cooperative_id == cooperative_id,
            func.lower(CollectionPoint.collection_name) == name.lower(),
        )
        if exclude_id is not None:
            query = query.where(CollectionPoint.collection_point_id != exclude_id)
        return self.db.scalar(query) is not None

    def create(self, user, payload) -> CollectionPoint:
        cooperative_id = require_admin(user)
        name = payload.collection_name.strip()

        if len(name) < 2:
            raise ServiceError(422, NAME_TOO_SHORT)

        if self._name_exists(cooperative_id, name):
            raise ServiceError(409, NAME_EXISTS)

        point = CollectionPoint(
            cooperative_id=cooperative_id,
            collection_name=name,
            status=AccountStatus.active,
        )

        try:
            self.db.add(point)
            self.db.flush()
            self.audit.record(
                user,
                "create_collection_point",
                "collection_point",
                point.collection_point_id,
                new_values={
                    "collection_name": point.collection_name,
                    "status": AccountStatus.active.value,
                },
            )
            commit_session(self.db)
            self.db.refresh(point)
            return point
        except Exception:
            self.db.rollback()
            raise

    def list_points(self, user, status: AccountStatus | None = None):
        cooperative_id = require_staff(user)

        query = select(CollectionPoint).where(CollectionPoint.cooperative_id == cooperative_id)

        if role_of(user) == UserRole.agent.value:
            if user.collection_point_id is None:
                return []
            query = query.where(CollectionPoint.collection_point_id == user.collection_point_id)

        if status is not None:
            query = query.where(CollectionPoint.status == status)

        return list(self.db.scalars(query.order_by(CollectionPoint.collection_name)).all())

    def get_point(self, user, point_id: UUID) -> CollectionPoint:
        return self._get_owned_point(user, point_id)

    def update(self, user, point_id: UUID, payload) -> CollectionPoint:
        require_admin(user)
        point = self._get_owned_point(user, point_id)

        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not changes:
            raise ServiceError(422, "Provide at least one field to update.")

        if "collection_name" in changes:
            name = changes["collection_name"].strip()
            if len(name) < 2:
                raise ServiceError(422, NAME_TOO_SHORT)
            if self._name_exists(point.cooperative_id, name, point.collection_point_id):
                raise ServiceError(409, NAME_EXISTS)
            changes["collection_name"] = name

        old_values = {k: str(enum_value(getattr(point, k))) for k in changes}

        try:
            for key, value in changes.items():
                setattr(point, key, value)

            self.audit.record(
                user,
                "update_collection_point",
                "collection_point",
                point.collection_point_id,
                old_values=old_values,
                new_values={k: str(enum_value(v)) for k, v in changes.items()},
            )
            commit_session(self.db)
            self.db.refresh(point)
            return point
        except Exception:
            self.db.rollback()
            raise

    def deactivate(self, user, point_id: UUID) -> CollectionPoint:
        require_admin(user)
        point = self._get_owned_point(user, point_id)

        if point.status == AccountStatus.inactive:
            return point

        old_status = point.status.value

        try:
            point.status = AccountStatus.inactive
            self.audit.record(
                user,
                "deactivate_collection_point",
                "collection_point",
                point.collection_point_id,
                old_values={"status": old_status},
                new_values={"status": AccountStatus.inactive.value},
            )
            commit_session(self.db)
            self.db.refresh(point)
            return point
        except Exception:
            self.db.rollback()
            raise