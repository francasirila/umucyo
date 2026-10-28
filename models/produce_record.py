import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.enums import DeliveryStatus


class ProduceRecord(Base):
    __tablename__ = "produce_record"

    produce_record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    produce_price_id = Column(UUID(as_uuid=True), ForeignKey("produce_price.produce_price_id"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmer.user_id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("weighing_device.device_id"), nullable=False)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=False)
    delivery_status = Column(Enum(DeliveryStatus, name="delivery_status"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=False)
    gross_weight_kg = Column(Numeric(10, 3), nullable=False)
    agent_notes = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cooperative = relationship("Cooperative", back_populates="produce_records")
    produce_price = relationship("ProducePrice", back_populates="produce_records")
    farmer = relationship("Farmer", back_populates="produce_records")
    device = relationship("WeighingDevice", back_populates="produce_records")
    collection_point = relationship("CollectionPoint", back_populates="produce_records")
    agent = relationship("CooperativeUser", back_populates="produce_records")
