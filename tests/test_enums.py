import pytest
from models.enums import (
    AccountStatus,
    DeliveryStatus,
    DeviceStatus,
    IssueCategory,
    MessageChannel,
    MessageDirection,
    MessageStatus,
    MessageType,
    PaymentStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
)


@pytest.mark.parametrize(
    "role,value",
    [(UserRole.ADMIN, "admin"), (UserRole.AGENT, "agent"), (UserRole.FARMER, "farmer")],
)
def test_user_role_values(role, value):
    assert role.value == value


@pytest.mark.parametrize(
    "enum_type",
    [
        AccountStatus,
        DeliveryStatus,
        DeviceStatus,
        IssueCategory,
        MessageChannel,
        MessageDirection,
        MessageStatus,
        MessageType,
        PaymentStatus,
        TaskPriority,
        TaskStatus,
        UserRole,
    ],
)
def test_enums_are_enumerations(enum_type):
    assert len(list(enum_type)) > 0


@pytest.mark.parametrize(
    "enum_type",
    [
        AccountStatus,
        DeliveryStatus,
        DeviceStatus,
        IssueCategory,
        MessageChannel,
        MessageDirection,
        MessageStatus,
        MessageType,
        PaymentStatus,
        TaskPriority,
        TaskStatus,
        UserRole,
    ],
)
def test_enum_values_are_strings(enum_type):
    assert all(isinstance(item.value, str) for item in enum_type)


def test_account_status_values():
    assert {item.value for item in AccountStatus} == {"active", "inactive"}


def test_delivery_status_values():
    assert {item.value for item in DeliveryStatus} == {"accepted", "rejected"}


def test_payment_status_values():
    assert {item.value for item in PaymentStatus} == {"pending", "paid", "failed"}


def test_task_status_values():
    assert {item.value for item in TaskStatus} == {
        "open",
        "in_progress",
        "completed",
        "cancelled",
    }
