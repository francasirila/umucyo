import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import DeviceStatus


class WeighingDevice(Base):
    __tablename__ = "weighing_device"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_point_id = Column(
        UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=False, index=True
    )
    serial_number = Column(String(100), nullable=False)
    status = Column(
        Enum(DeviceStatus, name="device_status"), nullable=False, default=DeviceStatus.ACTIVE, server_default="active"
    )
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    collection_point = relationship("CollectionPoint", back_populates="weighing_devices")
    produce_records = relationship("ProduceRecord", back_populates="device")
