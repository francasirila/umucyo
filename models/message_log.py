import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base
from models.enums import (
    IssueCategory,
    MessageChannel,
    MessageDirection,
    MessageStatus,
    MessageType,
)


class MessageLog(Base):
    __tablename__ = "message_log"

    message_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    farmer_id = Column(
        UUID(as_uuid=True), ForeignKey("farmer.farmer_id"), nullable=False, index=True
    )
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    direction = Column(Enum(MessageDirection, name="message_direction"), nullable=False)
    channel = Column(Enum(MessageChannel, name="message_channel"), nullable=False)
    message_type = Column(Enum(MessageType, name="message_type"), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(Enum(IssueCategory, name="issue_category"), nullable=True)
    status = Column(Enum(MessageStatus, name="message_status"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    provider_message_id = Column(String(150), nullable=True, unique=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cooperative = relationship(
        "Cooperative",
        back_populates="message_logs",
        foreign_keys=[cooperative_id],
    )

    farmer = relationship(
        "Farmer",
        back_populates="message_logs",
    )
