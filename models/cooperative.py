import uuid
from sqlalchemy import Column, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.enums import CooperativeStatus


class Cooperative(Base):
    __tablename__ = "cooperative"

    cooperative_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=False)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(Enum(CooperativeStatus, name="cooperative_status"), nullable=False, default=CooperativeStatus.active)

    users = relationship("User", back_populates="cooperative")
    collection_points = relationship("CollectionPoint", back_populates="cooperative")
    produce_prices = relationship("ProducePrice", back_populates="cooperative")
    produce_records = relationship("ProduceRecord", back_populates="cooperative")
    tasks = relationship("Task", back_populates="cooperative")
