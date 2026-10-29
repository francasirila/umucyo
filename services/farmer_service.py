import uuid
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ServiceError
from database import commit_session
from models.collection_point import CollectionPoint
from models.enums import AccountStatus, UserRole
from models.farmer import Farmer
from schemas.users import FarmerCreate
from services.access import get_active_point, require_staff, role_of
from services.audit_service import AuditService
from services.sms_service import normalize_phone, send_sms

logger = logging.getLogger(__name__)


class FarmerService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def register_farmer(self, current_user, payload: FarmerCreate) -> dict:
        require_staff(current_user)
        point = get_active_point(self.db, current_user, payload.collection_point_id)

        phone = normalize_phone(payload.phone_number)

        if self.db.scalar(select(Farmer.user_id).where(Farmer.phone_number == phone)):
            raise ServiceError(409, "A farmer with this phone number already exists.")

        farmer = Farmer(
            farmer_id=uuid.uuid4(),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            user_type=UserRole.farmer,
            status=AccountStatus.active,
            phone_number=phone,
            collection_point_id=point.collection_point_id,
            registered_by_user_id=current_user.user_id,
        )

        try:
            self.db.add(farmer)
            self.db.flush()
            self.audit.record(
                current_user,
                "register_farmer",
                "user",
                farmer.user_id,
                new_values={
                    "phone_number": phone,
                    "collection_point_id": str(point.collection_point_id),
                },
            )
            commit_session(self.db)
            self.db.refresh(farmer)
        except IntegrityError as exc:
            self.db.rollback()
            raise ServiceError(409, "A farmer with these details already exists.") from exc

        try:
            sms_sent = bool(
                send_sms(
                    phone,
                    f"Hello {farmer.first_name}, your Umucyo farmer account was "
                    "created successfully. You can now use Umucyo through USSD.",
                )
            )
        except Exception:
            logger.exception("Farmer confirmation SMS failed")
            sms_sent = False

        return {
            "message": "Farmer registered successfully.",
            "farmer": farmer,
            "sms_sent": sms_sent,
        }

    def _farmer_scope(self, current_user):
        cooperative_id = require_staff(current_user)
        stmt = (
            select(Farmer)
            .join(CollectionPoint, Farmer.collection_point_id == CollectionPoint.collection_point_id)
            .where(CollectionPoint.cooperative_id == cooperative_id)
        )
        if role_of(current_user) == UserRole.agent.value:
            stmt = stmt.where(Farmer.collection_point_id == current_user.collection_point_id)
        return stmt

    def list_farmers(self, current_user, collection_point_id: UUID | None = None):
        stmt = self._farmer_scope(current_user)
        if collection_point_id:
            stmt = stmt.where(Farmer.collection_point_id == collection_point_id)
        return list(self.db.scalars(stmt.order_by(Farmer.created_at.desc())))

    def get_farmer(self, current_user, farmer_id: UUID):
        farmer = self.db.scalar(self._farmer_scope(current_user).where(Farmer.user_id == farmer_id))
        if farmer is None:
            raise ServiceError(404, "Farmer not found.")
        return farmer
