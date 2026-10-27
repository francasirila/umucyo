import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class ProducePrice(Base):
    __tablename__ = "produce_price"

    produce_price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    unit = Column(String(20), nullable=False, default="kg", server_default="kg")
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cooperative_admin = relationship("User", foreign_keys=[cooperative_admin_id])
    created_by = relationship("User", back_populates="created_prices", foreign_keys=[created_by_user_id])
    produce_records = relationship("ProduceRecord", back_populates="produce_price")
