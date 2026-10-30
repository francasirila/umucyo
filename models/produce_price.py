import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class ProducePrice(Base):
    __tablename__ = "produce_price"

    produce_price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cooperative = relationship("Cooperative", back_populates="produce_prices")
    created_by = relationship("CooperativeUser", back_populates="created_prices")
    produce_records = relationship("ProduceRecord", back_populates="produce_price")
    payment_transactions = relationship("PaymentTransaction", back_populates="produce_price")
