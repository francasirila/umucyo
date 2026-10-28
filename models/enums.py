from enum import Enum


class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class CooperativeStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class UserType(str, Enum):
    farmer = "farmer"
    cooperative_admin = "admin"
    cooperative_agent = "agent"


class DeliveryStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"
    partially_accepted = "partially_accepted"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageChannel(str, Enum):
    SMS = "SMS"
    USSD = "USSD"


class MessageType(str, Enum):
    report = "report"
    question = "question"
    weighing_notice = "weighing_notice"
    price_change = "price_change"
    payment_notice = "payment_notice"
    response = "response"
    other = "other"


class MessageCategory(str, Enum):
    financial = "financial"
    non_financial = "non_financial"


class MessageStatus(str, Enum):
    received = "received"
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class TaskPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class UserRole(str, Enum):
    admin = "admin"
    agent = "agent"
    farmer = "farmer"


class IssueCategory(str, Enum):
    financial = "financial"
    non_financial = "non_financial"
