from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session
from core.exceptions import ServiceError
from models.enums import TaskStatus
from models.task import Task
from repositories import task as repo
from schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_related_records(
        self,
        cooperative_id: UUID,
        created_by_user_id: UUID | None = None,
        assigned_to_user_id: UUID | None = None,
        collection_point_id: UUID | None = None,
    ) -> None:
        cooperative = repo.get_cooperative(self.db, cooperative_id)

        if cooperative is None:
            raise ServiceError(404, "Cooperative not found.")

        for user_id, label in (
            (created_by_user_id, "Creator"),
            (assigned_to_user_id, "Assignee"),
        ):
            if user_id is None:
                continue

            user = repo.get_cooperative_user(self.db, user_id)

            if user is None or user.cooperative_id != cooperative_id:
                raise ServiceError(
                    422,
                    f"{label} must belong to the specified cooperative.",
                )

        if collection_point_id is not None:
            point = repo.get_collection_point(
                self.db,
                collection_point_id,
            )

            if point is None or point.cooperative_id != cooperative_id:
                raise ServiceError(
                    422,
                    "Collection point must belong to the specified cooperative.",
                )

    def create(self, payload: TaskCreate) -> Task:
        values = payload.model_dump()

        self._validate_related_records(
            cooperative_id=values["cooperative_id"],
            created_by_user_id=values["created_by_user_id"],
            assigned_to_user_id=values["assigned_to_user_id"],
            collection_point_id=values.get("collection_point_id"),
        )

        try:
            task = Task(**values)
            return repo.create(self.db, task)
        except Exception:
            self.db.rollback()
            raise

    def list_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        if skip < 0:
            raise ServiceError(422, "Skip cannot be negative.")

        if not 1 <= limit <= 100:
            raise ServiceError(
                422,
                "Limit must be between 1 and 100.",
            )

        return repo.list_all(
            self.db,
            skip=skip,
            limit=limit,
        )

    def get_task(self, task_id: UUID) -> Task:
        task = repo.get_by_id(self.db, task_id)

        if task is None:
            raise ServiceError(404, "Task not found.")

        return task

    def update(
        self,
        task_id: UUID,
        payload: TaskUpdate,
    ) -> Task:
        task = self.get_task(task_id)
        changes = payload.model_dump(exclude_unset=True)

        if not changes:
            raise ServiceError(
                422,
                "Provide at least one field to update.",
            )

        if "assigned_to_user_id" in changes:
            if changes["assigned_to_user_id"] is None:
                raise ServiceError(
                    422,
                    "Assignee cannot be null.",
                )

            self._validate_related_records(
                cooperative_id=task.cooperative_id,
                assigned_to_user_id=changes["assigned_to_user_id"],
            )

        if "collection_point_id" in changes and changes["collection_point_id"] is not None:
            self._validate_related_records(
                cooperative_id=task.cooperative_id,
                collection_point_id=changes["collection_point_id"],
            )

        for field in ("description", "priority", "status"):
            if field in changes and changes[field] is None:
                raise ServiceError(
                    422,
                    f"{field.replace('_', ' ').capitalize()} cannot be null.",
                )

        if "description" in changes:
            description = changes["description"].strip()

            if not description:
                raise ServiceError(
                    422,
                    "Description cannot be empty or whitespace.",
                )

            changes["description"] = description

        if changes.get("status") == TaskStatus.completed:
            changes["completed_at"] = datetime.now(timezone.utc)
        elif "status" in changes and changes["status"] != TaskStatus.completed:
            changes["completed_at"] = None

        try:
            updated_task = repo.update(
                self.db,
                task,
                changes,
            )
            return updated_task
        except Exception:
            self.db.rollback()
            raise

    def delete(self, task_id: UUID) -> None:
        task = self.get_task(task_id)

        try:
            repo.delete(self.db, task)
        except Exception:
            self.db.rollback()
            raise
