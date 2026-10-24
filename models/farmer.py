import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import AccountStatus


class Farmer(Base):
    __tablename__ = "farmer"

    farmer_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=False,
        index=True,
    )
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    registered_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False
    )
    status = Column(
        Enum(AccountStatus, name="farmer_status"),
        nullable=False,
        default=AccountStatus.active,
        server_default="active",
    )
    phone_number = Column(String(20), nullable=False, unique=True)

    cooperative = relationship(
        "Cooperative",
        back_populates="farmers",
    )

    produce_records = relationship(
        "ProduceRecord",
        back_populates="farmer",
    )

    payment_transactions = relationship(
        "PaymentTransaction",
        back_populates="farmer",
    )

    message_logs = relationship(
        "MessageLog",
        back_populates="farmer",
    )

    tasks = relationship(
        "Task",
        back_populates="farmer",
    )
