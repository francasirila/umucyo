from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.collection_point import CollectionPoint
from models.enums import AccountStatus


def add_record(db, model, data: dict):
    record = model(**data)
    db.add(record)
    db.flush()
    return record


def get_record(db, model, record_id):
    return db.get(model, record_id)


def update_record(db, record, data: dict):
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def delete_record(db, record):
    db.delete(record)
    db.flush()


class CollectionPointRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, collection_point_id: UUID):
        return get_record(self.db, CollectionPoint, collection_point_id)

    def get_by_name(self, cooperative_id: UUID, name: str):
        return self.db.scalar(
            select(CollectionPoint).where(
                CollectionPoint.cooperative_id == cooperative_id,
                func.lower(CollectionPoint.collection_name) == name.strip().lower(),
            )
        )

    def list_by_cooperative(
        self,
        cooperative_id: UUID,
        status: AccountStatus | None = None,
    ):
        query = select(CollectionPoint).where(CollectionPoint.cooperative_id == cooperative_id)

        if status is not None:
            query = query.where(CollectionPoint.status == status)

        return list(self.db.scalars(query.order_by(CollectionPoint.collection_name)).all())

    def create(self, data: dict):
        return add_record(self.db, CollectionPoint, data)

    def update(self, point, data):
        return update_record(self.db, point, data)

    def delete(self, point):
        delete_record(self.db, point)
