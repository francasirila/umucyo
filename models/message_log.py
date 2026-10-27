import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    message_type = Column(Enum(MessageType, name="message_type"), nullable=False)
    category = Column(Enum(IssueCategory, name="issue_category"), nullable=True)
    channel = Column(
        Enum(MessageChannel, name="message_channel"),
        nullable=False,
        default=MessageChannel.SMS,
    )
    direction = Column(Enum(MessageDirection, name="message_direction"), nullable=False)
    status = Column(
        Enum(MessageStatus, name="message_status"),
        nullable=False,
        default=MessageStatus.RECEIVED,
    )
    content = Column(Text, nullable=True)
    provider_message_id = Column(String(100), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    farmer = relationship("User", back_populates="farmer_messages", foreign_keys=[farmer_id])
    reviewed_by_user = relationship("User", back_populates="reviewed_messages", foreign_keys=[reviewed_by])
    tasks = relationship("Task", back_populates="message")
