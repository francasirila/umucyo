import uuid
from models.collection_point import CollectionPoint
from models.enums import AccountStatus


def create_mock_cp():
    return CollectionPoint(
        collection_point_id=uuid.uuid4(),
        cooperative_id=uuid.uuid4(),
        collection_name="Main",
        location="Kigali",
        status=AccountStatus.active,
    )


def test_collection_point_creation():
    assert create_mock_cp().collection_name == "Main"


def test_collection_point_missing_name():
    cp = create_mock_cp()
    cp.collection_name = None
    assert cp.collection_name is None


def test_collection_point_special_chars():
    cp = create_mock_cp()
    cp.collection_name = "Center #1"
    assert "#" in cp.collection_name


def test_collection_point_inactive():
    cp = create_mock_cp()
    cp.status = AccountStatus.inactive
    assert cp.status == AccountStatus.inactive
