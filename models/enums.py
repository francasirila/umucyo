import enum


class CooperativeStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"


class AccountStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class DeliveryStatus(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"


class DeviceStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageChannel(str, enum.Enum):
    SMS = "SMS"
    USSD = "USSD"


class MessageType(str, enum.Enum):
    report = "report"
    question = "question"
    weighing_notice = "weighing_notice"
    price_change = "price_change"
    payment_notice = "payment_notice"
    response = "response"
    other = "other"


class IssueCategory(str, enum.Enum):
    financial = "financial"
    non_financial = "non_financial"


class MessageStatus(str, enum.Enum):
    received = "received"
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class TaskPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TaskStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
