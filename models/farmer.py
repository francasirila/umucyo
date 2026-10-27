from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.enums import UserType
from models.user import User


class Farmer(User):
    __tablename__ = "farmer"

    farmer_id = Column(UUID(as_uuid=True), unique=False, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey("collection_point.collection_point_id"), nullable=False)
    registered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    phone_number = Column(String(20), nullable=False)

    collection_point = relationship("CollectionPoint", back_populates="farmers")
    registered_by = relationship("User", foreign_keys=[registered_by_user_id])
    produce_records = relationship("ProduceRecord", back_populates="farmer")
    payment_transactions = relationship("PaymentTransaction", back_populates="farmer")
    message_logs = relationship("MessageLog", back_populates="farmer")
    user = relationship(
        "User",
        back_populates="farmer",
        foreign_keys=[user_id],
    )
    __mapper_args__ = {
        "polymorphic_identity": UserType.farmer,
        "inherit_condition": user_id == User.user_id,
    }
