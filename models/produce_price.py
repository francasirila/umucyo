import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from database import Base


class ProducePrice(Base):
    __tablename__ = "produce_price"
    __table_args__ = (
        CheckConstraint("price_per_unit >= 0", name="ck_produce_price_nonnegative"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_produce_price_effective_dates",
        ),
    )

    produce_price_id = Column(
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
    unit = Column(String(20), nullable=False, default="kg", server_default="kg")
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cooperative = relationship(
        "Cooperative",
        back_populates="produce_prices",
    )

    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )
