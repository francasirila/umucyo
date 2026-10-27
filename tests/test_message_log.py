import pytest
from models import MessageLog, MessageStatus
from tests.helpers import column, foreign_key_targets, relationship_names


@pytest.mark.parametrize(
    "name",
    [
        "message_id",
        "farmer_id",
        "direction",
        "channel",
        "message_type",
        "content",
        "category",
        "status",
        "sent_at",
        "reviewed_by",
        "received_at",
        "provider_message_id",
        "created_at",
    ],
)
def test_message_columns_exist(name):
    assert name in MessageLog.__table__.columns


@pytest.mark.parametrize("name", ["message_id", "farmer_id", "direction", "channel", "message_type", "status", "created_at"])
def test_message_required_columns(name):
    assert column(MessageLog, name).nullable is False


@pytest.mark.parametrize("name", ["content", "category", "sent_at", "reviewed_by", "received_at", "provider_message_id"])
def test_message_optional_columns(name):
    assert column(MessageLog, name).nullable is True


def test_message_farmer_references_users():
    assert foreign_key_targets(MessageLog, "farmer_id") == {"users.user_id"}


def test_message_reviewer_references_users():
    assert foreign_key_targets(MessageLog, "reviewed_by") == {"users.user_id"}


@pytest.mark.parametrize("name", ["farmer", "reviewed_by_user", "tasks"])
def test_message_relationships_exist(name):
    assert name in relationship_names(MessageLog)


def test_message_default_status():
    assert MessageLog.status.default.arg == MessageStatus.RECEIVED


def test_provider_message_id_is_unique():
    pass
