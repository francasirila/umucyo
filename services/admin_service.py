from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ServiceError
from core.security import get_password_hash
from models.cooperative_user import CooperativeAdmin, CooperativeUser
from models.enums import AccountStatus, UserRole
from schemas.users import AdminCreate
from services.access import require_admin
from services.audit_service import AuditService

EMAIL_EXISTS = "An account with this email already exists."


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def create_admin(self, current_user, payload: AdminCreate) -> CooperativeAdmin:
        cooperative_id = require_admin(current_user)
        email = str(payload.email).strip().lower()

        if self.db.scalar(select(CooperativeUser.user_id).where(CooperativeUser.email == email)):
            raise ServiceError(409, EMAIL_EXISTS)

        user = CooperativeAdmin(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            user_type=UserRole.admin,
            status=AccountStatus.active,
            email=email,
            password_hash=get_password_hash(payload.password),
            cooperative_id=cooperative_id,
            registered_by_user_id=current_user.user_id,
        )

        try:
            self.db.add(user)
            self.db.flush()

            self.audit.record(
                current_user,
                "create_admin",
                "user",
                user.user_id,
                new_values={"email": email},
            )

            self.db.commit()
            self.db.refresh(user)
            return user

        except IntegrityError as exc:
            self.db.rollback()
            if "email" in str(exc.orig).lower():
                raise ServiceError(409, EMAIL_EXISTS) from exc
            raise
        except Exception:
            self.db.rollback()
            raise