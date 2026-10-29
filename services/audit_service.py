from uuid import UUID

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(self, user, action: str, entity_type: str, entity_id: UUID, old_values=None, new_values=None):
        if user is None:
            return None
        record = AuditLog(
            user_id=user.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
        )
        self.db.add(record)
        return record
