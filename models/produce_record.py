import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import DeliveryStatus


class ProduceRecord(Base):
    __tablename__ = "produce_record"
    __table_args__ = (
        CheckConstraint("gross_weight_kg >= 0", name="ck_produce_gross_nonnegative"),
        CheckConstraint(
            "rejected_weight_kg >= 0 AND rejected_weight_kg <= gross_weight_kg",
            name="ck_produce_rejected_weight",
        ),
        CheckConstraint(
            "accepted_weight_kg >= 0", name="ck_produce_accepted_nonnegative"
        ),
        CheckConstraint(
            "accepted_weight_kg = gross_weight_kg - rejected_weight_kg",
            name="ck_produce_accepted_weight",
        ),
        CheckConstraint("amount >= 0", name="ck_produce_amount_nonnegative"),
    )

    produce_record_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    produce_price_id = Column(
        UUID(as_uuid=True), ForeignKey("produce_price.produce_price_id"), nullable=False
    )
    farmer_id = Column(
        UUID(as_uuid=True), ForeignKey("farmer.farmer_id"), nullable=False, index=True
    )
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("weighing_device.device_id"), nullable=False
    )
    payment_transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payment_transaction.payment_transaction_id"),
        nullable=True,
        index=True,
    )
    collection_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_point.collection_point_id"),
        nullable=False,
        index=True,
    )
    delivery_status = Column(
        Enum(DeliveryStatus, name="delivery_status"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    gross_weight_kg = Column(Numeric(10, 3), nullable=False)
    rejected_weight_kg = Column(
        Numeric(10, 3), nullable=False, default=Decimal("0"), server_default="0"
    )
    accepted_weight_kg = Column(Numeric(10, 3), nullable=False)
    agent_notes = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    recorded_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cooperative = relationship(
        "Cooperative",
        back_populates="produce_records",
    )

    farmer = relationship(
        "Farmer",
        back_populates="produce_records",
    )

    collection_point = relationship(
        "CollectionPoint",
        back_populates="produce_records",
    )

    weighing_device = relationship(
        "WeighingDevice",
        back_populates="produce_records",
    )

    produce_price = relationship("ProducePrice", foreign_keys=[produce_price_id])

    agent = relationship("User", foreign_keys=[user_id])
