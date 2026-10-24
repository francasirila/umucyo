import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import PaymentStatus


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_payment_quantity_nonnegative"),
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        CheckConstraint(
            "(status = 'paid') = (payment_date IS NOT NULL)",
            name="ck_payment_paid_date",
        ),
    )

    payment_transaction_id = Column(
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
    farmer_id = Column(
        UUID(as_uuid=True), ForeignKey("farmer.farmer_id"), nullable=False, index=True
    )
    initiated_by = Column(
        UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False
    )
    batch_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    period = Column(Date, nullable=False, index=True)

    quantity = Column(Numeric(10, 3), nullable=False)
    amount = Column(Integer, nullable=False)

    status = Column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.pending,
        server_default="pending",
        index=True,
    )
    transaction_reference = Column(String(150), nullable=False, unique=True)
    provider_transfer_id = Column(String(100), nullable=True)
    failure_reason = Column(Text, nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cooperative = relationship("Cooperative", back_populates="payment_transactions")
    farmer = relationship("Farmer", back_populates="payment_transactions")
    initiator = relationship("User", foreign_keys=[initiated_by])
