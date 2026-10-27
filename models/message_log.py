import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.enums import MessageCategory, MessageChannel, MessageDirection, MessageStatus, MessageType


class MessageLog(Base):
    __tablename__ = "message_log"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmer.user_id"), nullable=False)
    direction = Column(Enum(MessageDirection, name="message_direction"), nullable=False)
    channel = Column(Enum(MessageChannel, name="message_channel"), nullable=False)
    message_type = Column(Enum(MessageType, name="message_type"), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(Enum(MessageCategory, name="message_category"), nullable=True)
    status = Column(Enum(MessageStatus, name="message_status"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("cooperative_user.user_id"), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    provider_message_id = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    farmer = relationship("Farmer", back_populates="message_logs")
    reviewer = relationship("CooperativeUser", back_populates="reviewed_messages")
    tasks = relationship("Task", back_populates="message")
