from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.collection_point import CollectionPoint
from models.agent_invitation import AgentInvitation
from models.cooperative_user import CooperativeAdmin, CooperativeAgent, CooperativeUser
from models.farmer import Farmer
from models.enums import AccountStatus, UserRole
from models.user import User
from database import add_record, get_record, update_record


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID):
        return get_record(self.db, User, user_id)

    def get_by_email(self, email: str):
        return self.db.scalar(select(CooperativeUser).where(CooperativeUser.email == email.strip().lower()))

    def get_by_phone_number(self, phone_number: str):
        return self.db.scalar(select(Farmer).where(Farmer.phone_number == phone_number.strip()))

    def get_by_invitation_hash(self, token_hash: str):
        invitation = self.db.scalar(
            select(AgentInvitation).where(
                AgentInvitation.token_hash == token_hash,
                AgentInvitation.accepted_at.is_(None),
            )
        )

        return self.db.get(CooperativeUser, invitation.user_id) if invitation else None

    def create(self, data: dict):
        data = dict(data)
        raw = data.pop("role", None) or data.get("user_type")
        role = UserRole(getattr(raw, "value", raw))
        data["user_type"] = role

        model = {
            UserRole.admin: CooperativeAdmin,
            UserRole.agent: CooperativeAgent,
            UserRole.farmer: Farmer,
        }[role]

        return add_record(self.db, model, data)

    def update(self, user, data):
        return update_record(self.db, user, data)

    def list_for_cooperative(
        self,
        cooperative_id: UUID,
        role: UserRole | None = None,
        collection_point_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        user_ids = (
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

        query = select(User).where(User.user_id.in_(user_ids))

        if role is not None:
            query = query.where(User.role == role)

        if collection_point_id is not None:
            farmer_ids = select(Farmer.user_id).where(Farmer.collection_point_id == collection_point_id)
            query = query.where(User.user_id.in_(farmer_ids))

        return list(self.db.scalars(query.order_by(User.created_at.desc()).offset(skip).limit(limit)).all())

    def list_farmers_at_points(
        self,
        point_ids: list[UUID],
        collection_point_id: UUID | None = None,
        since: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        if not point_ids:
            return []

        query = select(Farmer).where(Farmer.collection_point_id.in_(point_ids))

        if collection_point_id is not None:
            query = query.where(Farmer.collection_point_id == collection_point_id)

        if since is not None:
            query = query.where(Farmer.created_at >= since)

        return list(self.db.scalars(query.order_by(User.created_at.desc()).offset(skip).limit(limit)).all())

    def get_active_farmer_by_phone_number(self, phone_number: str):
        return self.db.scalar(
            select(Farmer).where(
                Farmer.phone_number == phone_number.strip(),
                Farmer.status == AccountStatus.active,
            )
        )
