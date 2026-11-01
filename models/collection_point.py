import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.enums import AccountStatus


class CollectionPoint(Base):
    __tablename__ = "collection_point"

    collection_point_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_id = Column(UUID(as_uuid=True), ForeignKey("cooperative.cooperative_id"), nullable=False)
    collection_name = Column(String(100), nullable=False)
    status = Column(Enum(AccountStatus, name="collection_point_status"), nullable=False, default=AccountStatus.active)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cooperative = relationship("Cooperative", back_populates="collection_points")
    assignments = relationship("AgentAssignment", back_populates="collection_point")
    weighing_devices = relationship("WeighingDevice", back_populates="collection_point")
    farmers = relationship("Farmer", back_populates="collection_point")
    produce_records = relationship("ProduceRecord", back_populates="collection_point")
    cooperative_users = relationship("CooperativeUser", back_populates="collection_point", foreign_keys="CooperativeUser.collection_point_id")
    tasks = relationship("Task", back_populates="collection_point")
