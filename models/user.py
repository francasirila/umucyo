import uuid
from sqlalchemy import Column, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import synonym
from database import Base
from models.enums import AccountStatus, UserRole


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(Enum(AccountStatus, name="account_status"), nullable=False, default=AccountStatus.active)
    user_type = Column("user_type", Enum(UserRole, name="user_role"), nullable=False)
    role = synonym("user_type")
    __mapper_args__ = {"polymorphic_on": user_type}
