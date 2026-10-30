import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class PaymentReport(Base):
    __tablename__ = "payment_report"

    payment_report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cooperative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cooperative.cooperative_id"),
        nullable=False,
        index=True,
    )
    farmer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("farmer.user_id"),
        nullable=False,
        index=True,
    )
    report_type = Column(String(30), nullable=False)
    reported_month_start = Column(Date, nullable=False)
    reported_month_label = Column(String(40), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    confirmation_sms_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    cooperative = relationship("Cooperative")
    farmer = relationship("Farmer")
