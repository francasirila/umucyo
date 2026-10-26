import uuid
from models.cooperative import Cooperative
from models.enums import CooperativeStatus


def create_mock_coop():
    return Cooperative(
        cooperative_id=uuid.uuid4(),
        cooperative_name="Test Coop",
        location="Kigali",
        phone_number="0788",
        email="a@b.c",
        status=CooperativeStatus.active,
    )


def test_cooperative_creation():
    assert create_mock_coop().cooperative_name == "Test Coop"


def test_cooperative_invalid_status():
    coop = create_mock_coop()
    coop.status = "invalid"
    assert coop.status == "invalid"


def test_cooperative_unicode():
    coop = create_mock_coop()
    coop.cooperative_name = "Icyayi (Coffee)"
    assert "(Coffee)" in coop.cooperative_name


def test_cooperative_empty_name():
    coop = create_mock_coop()
    coop.cooperative_name = ""
    assert coop.cooperative_name == ""


def test_cooperative_long_name():
    coop = create_mock_coop()
    coop.cooperative_name = "A" * 150
    assert len(coop.cooperative_name) == 150


def test_cooperative_missing_email():
    coop = create_mock_coop()
    coop.email = None
    assert coop.email is None
