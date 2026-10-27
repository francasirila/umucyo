import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.enums import AccountStatus


class CollectionPoint(Base):
    __tablename__ = "collection_point"

    collection_point_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=False)
    status = Column(
        Enum(AccountStatus, name="account_status"), nullable=False, default=AccountStatus.ACTIVE, server_default="active"
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cooperative_admin_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True
    )

    cooperative_admin = relationship("User", back_populates="managed_collection_points", foreign_keys=[cooperative_admin_id])
    farmers = relationship("User", back_populates="farmer_collection_point", foreign_keys="User.collection_point_id")
    agent_assignments = relationship("AgentAssignment", back_populates="collection_point")
    weighing_devices = relationship("WeighingDevice", back_populates="collection_point")
    produce_records = relationship("ProduceRecord", back_populates="collection_point")
    tasks = relationship("Task", back_populates="collection_point")
