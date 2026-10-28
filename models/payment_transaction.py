import uuid
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.types import Uuid
from database import Base
from models.enums import PaymentStatus
from sqlalchemy.orm import relationship


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"

    payment_transaction_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(Uuid(as_uuid=True), ForeignKey("farmer.user_id"), nullable=False)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    produce_price_id = Column(Uuid(as_uuid=True), ForeignKey("produce_price.produce_price_id"), nullable=False)
    produce_record_id = Column(Uuid(as_uuid=True), ForeignKey("produce_record.produce_record_id"), nullable=False)
    provider = Column(String(50), nullable=False, default="MTN")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_reference = Column(String(150), nullable=False)
    failure_reason = Column(Text, nullable=True)
    status = Column(Enum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.pending)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Uuid(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)

    farmer = relationship("Farmer", back_populates="payment_transactions")
    initiated_by = relationship("CooperativeUser", foreign_keys=[user_id], back_populates="initiated_payments")
    approved_by_user = relationship("CooperativeUser", foreign_keys=[approved_by], back_populates="approved_payments")
    produce_price = relationship("ProducePrice", back_populates="payment_transactions")
    produce_records = relationship("ProduceRecord", back_populates="payment_transaction")
