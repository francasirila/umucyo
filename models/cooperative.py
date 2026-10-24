import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from models.enums import CooperativeStatus
from database import Base


class Cooperative(Base):
    __tablename__ = "cooperative"

    cooperative_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status = Column(
        Enum(CooperativeStatus, name="cooperative_status"),
        nullable=False,
        default=CooperativeStatus.active,
        server_default="active",
    )
    users = relationship("User", back_populates="cooperative")
    farmers = relationship("Farmer", back_populates="cooperative")
    collection_points = relationship("CollectionPoint", back_populates="cooperative")
    agent_assignments = relationship("AgentAssignment", back_populates="cooperative")
    weighing_devices = relationship("WeighingDevice", back_populates="cooperative")
    produce_records = relationship("ProduceRecord", back_populates="cooperative")
    produce_prices = relationship("ProducePrice", back_populates="cooperative")
    payment_transactions = relationship(
        "PaymentTransaction", back_populates="cooperative"
    )
    message_logs = relationship("MessageLog", back_populates="cooperative")
    tasks = relationship("Task", back_populates="cooperative")
    audit_logs = relationship("AuditLog", back_populates="cooperative")
