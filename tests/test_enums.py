from models.enums import (
    CooperativeStatus,
    UserRole,
    AccountStatus,
    DeliveryStatus,
    DeviceStatus,
    PaymentStatus,
    MessageDirection,
    MessageChannel,
    MessageType,
    TaskPriority,
)


def test_cooperative_status_enum():
    assert CooperativeStatus.active.value == "active"


def test_user_role_enum():
    assert UserRole.admin.value == "admin"


def test_payment_status_enum():
    assert PaymentStatus.paid.value == "paid"


def test_message_channel_enum():
    assert MessageChannel.USSD.value == "USSD"


def test_account_status():
    assert AccountStatus.active.value == "active"


def test_delivery_status():
    assert DeliveryStatus.accepted.value == "accepted"


def test_device_status():
    assert DeviceStatus.active.value == "active"


def test_message_direction():
    assert MessageDirection.inbound.value == "inbound"


def test_message_type():
    assert MessageType.report.value == "report"


def test_task_priority():
    assert TaskPriority.high.value == "high"
