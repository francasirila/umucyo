from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from models.cooperative_user import CooperativeUser
from models.collection_point import CollectionPoint
from models.farmer import Farmer
from database import add_record


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict):
        return add_record(self.db, AuditLog, data)

    def list_for_cooperative(
        self,
        cooperative_id: UUID,
        entity_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        actors = (
            select(CooperativeUser.user_id)
            .where(CooperativeUser.cooperative_id == cooperative_id)
            .union(
                select(Farmer.user_id)
                .join(
                    CollectionPoint,
                    Farmer.collection_point_id == CollectionPoint.collection_point_id,
                )
                .where(CollectionPoint.cooperative_id == cooperative_id)
            )
        )

        query = select(AuditLog).where(AuditLog.user_id.in_(actors))

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        return list(self.db.scalars(query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)).all())
