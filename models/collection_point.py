import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import AccountStatus


class CollectionPoint(Base):
    __tablename__ = "collection_point"
    __table_args__ = (
        UniqueConstraint(
            "collection_point_id",
            "cooperative_id",
            name="uq_collection_point_id_cooperative",
        ),
    )

    collection_point_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    collection_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(
        Enum(AccountStatus, name="collection_point_status"),
        nullable=False,
        default=AccountStatus.active,
        server_default="active",
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cooperative = relationship(
        "Cooperative",
        back_populates="collection_points",
    )

    agent_assignments = relationship(
        "AgentAssignment",
        back_populates="collection_point",
    )

    weighing_devices = relationship(
        "WeighingDevice",
        back_populates="collection_point",
    )

    produce_records = relationship(
        "ProduceRecord",
        back_populates="collection_point",
    )

    tasks = relationship(
        "Task",
        back_populates="collection_point",
    )
