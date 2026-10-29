from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.login_otp import LoginOTP
from database import add_record


class OTPRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self, user_id: UUID) -> LoginOTP | None:
        statement = (
            select(LoginOTP)
            .where(
                LoginOTP.user_id == user_id,
                LoginOTP.consumed_at.is_(None),
            )
            .order_by(LoginOTP.created_at.desc())
        )

        return self.db.scalars(statement).first()

    def get_latest(self, user_id: UUID) -> LoginOTP | None:
        statement = select(LoginOTP).where(LoginOTP.user_id == user_id).order_by(LoginOTP.created_at.desc())

        return self.db.scalars(statement).first()

    def consume_active(
        self,
        user_id: UUID,
        consumed_at: datetime,
    ) -> None:
        self.db.execute(
            update(LoginOTP)
            .where(
                LoginOTP.user_id == user_id,
                LoginOTP.consumed_at.is_(None),
            )
            .values(consumed_at=consumed_at)
        )

    def create(self, data: dict) -> LoginOTP:
        return add_record(self.db, LoginOTP, data)
