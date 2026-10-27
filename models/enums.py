import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    FARMER = "farmer"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DeliveryStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(str, enum.Enum):
    SMS = "SMS"
    USSD = "USSD"


class MessageType(str, enum.Enum):
    REPORT = "report"
    QUESTION = "question"
    WEIGHING_NOTICE = "weighing_notice"
    PRICE_CHANGE = "price_change"
    PAYMENT_NOTICE = "payment_notice"
    RESPONSE = "response"
    OTHER = "other"


class IssueCategory(str, enum.Enum):
    FINANCIAL = "financial"
    NON_FINANCIAL = "non_financial"


class MessageStatus(str, enum.Enum):
    RECEIVED = "received"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
