from uuid import UUID

from sqlalchemy.orm import Session

from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.task import Task


def create(db: Session, task: Task) -> Task:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Task]:
    return db.query(Task).order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


def get_by_id(db: Session, task_id: UUID) -> Task | None:
    return db.query(Task).filter(Task.task_id == task_id).first()


def update(db: Session, task: Task, changes: dict) -> Task:
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def get_cooperative(db: Session, cooperative_id: UUID):
    return db.query(Cooperative).filter(Cooperative.cooperative_id == cooperative_id).first()


def get_cooperative_user(db: Session, user_id: UUID):
    return db.query(CooperativeUser).filter(CooperativeUser.user_id == user_id).first()


def get_collection_point(db: Session, collection_point_id: UUID):
    return db.query(CollectionPoint).filter(CollectionPoint.collection_point_id == collection_point_id).first()
