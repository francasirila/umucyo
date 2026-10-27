import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import DeliveryStatus


class ProduceRecord(Base):
    __tablename__ = "produce_record"

    produce_record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    device_id = Column(
        UUID(as_uuid=True), ForeignKey("weighing_device.device_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    produce_price_id = Column(
        UUID(as_uuid=True), ForeignKey("produce_price.produce_price_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payment_transaction.payment_transaction_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    collection_point_id = Column(
        UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    delivery_status = Column(Enum(DeliveryStatus, name="delivery_status"), nullable=False)
    gross_weight_kg = Column(Numeric(10, 3), nullable=False)
    rejected_weight_kg = Column(Numeric(10, 3), nullable=False)
    accepted_weight_kg = Column(Numeric(10, 3), nullable=False)
    agent_notes = Column(Text, nullable=False, default="")
    amount = Column(Numeric(12, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    produce_price = relationship("ProducePrice", back_populates="produce_records")
    farmer = relationship("User", back_populates="produce_records", foreign_keys=[farmer_id])
    agent = relationship("User", back_populates="farmer_produce_records", foreign_keys=[user_id])
    device = relationship("WeighingDevice", back_populates="produce_records")
    payment_transaction = relationship("PaymentTransaction", back_populates="produce_records")
    collection_point = relationship("CollectionPoint", back_populates="produce_records")
