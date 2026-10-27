import uuid

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import PaymentStatus


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"

    payment_transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    initiated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    provider = Column(String(50), nullable=False, default="Flutterwave", server_default="Flutterwave")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    transaction_reference = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(Enum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.PENDING)
    failure_reason = Column(String(500), nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)

    farmer = relationship("User", back_populates="farmer_payments", foreign_keys=[farmer_id])
    initiated_by = relationship("User", back_populates="initiated_payments", foreign_keys=[initiated_by_user_id])
    approved_by_user = relationship("User", back_populates="approved_payments", foreign_keys=[approved_by])
    produce_records = relationship("ProduceRecord", back_populates="payment_transaction")
