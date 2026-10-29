from enum import Enum


class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class CooperativeStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class DeliveryStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"
    partially_accepted = "partially_accepted"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


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
