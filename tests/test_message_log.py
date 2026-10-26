import uuid
from models.message_log import MessageLog
from models.enums import (
    MessageDirection,
    MessageChannel,
    MessageType,
    IssueCategory,
    MessageStatus,
)


def create_mock_message():
    return MessageLog(
        message_id=uuid.uuid4(),
        farmer_id=uuid.uuid4(),
        cooperative_id=uuid.uuid4(),
        direction=MessageDirection.inbound,
        channel=MessageChannel.USSD,
        message_type=MessageType.report,
        category=IssueCategory.financial,
        content="Help",
        status=MessageStatus.received,
    )


def test_message_creation():
    assert create_mock_message().content == "Help"


def test_message_sms_channel():
    msg = create_mock_message()
    msg.channel = MessageChannel.SMS
    assert msg.channel == MessageChannel.SMS


def test_message_empty_content():
    msg = create_mock_message()
    msg.content = ""
    assert msg.content == ""


def test_message_max_length():
    msg = create_mock_message()
    msg.content = "A" * 1000
    assert len(msg.content) == 1000


def test_message_unicode():
    msg = create_mock_message()
    msg.content = "Ntibyashyuwe (Leaf)"
    assert "(Leaf)" in msg.content


def test_message_outbound():
    msg = create_mock_message()
    msg.direction = MessageDirection.outbound
    assert msg.direction == MessageDirection.outbound


def test_message_special_chars():
    msg = create_mock_message()
    msg.content = "I need help! #urgent @admin"
    assert "@" in msg.content
