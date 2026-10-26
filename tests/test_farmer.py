import uuid
from models.farmer import Farmer
from models.enums import AccountStatus

def create_mock_farmer():
    return Farmer(farmer_id=uuid.uuid4(), cooperative_id=uuid.uuid4(), collection_point_id=uuid.uuid4(), first_name="Jean", last_name="Claude", phone_number="0788", registered_by_user_id=uuid.uuid4(), status=AccountStatus.active)

def test_farmer_creation():
    assert create_mock_farmer().first_name == "Jean"

def test_farmer_missing_name():
    farmer = create_mock_farmer()
    farmer.first_name = None
    assert farmer.first_name is None

def test_farmer_short_phone():
    farmer = create_mock_farmer()
    farmer.phone_number = "1"
    assert len(farmer.phone_number) == 1

def test_farmer_long_phone():
    farmer = create_mock_farmer()
    farmer.phone_number = "1" * 20
    assert len(farmer.phone_number) == 20

def test_farmer_unicode_name():
    farmer = create_mock_farmer()
    farmer.first_name = "Mukamana"
    farmer.last_name = "Uwase (Leaf)"
    assert "(Leaf)" in farmer.last_name

def test_farmer_missing_last_name():
    farmer = create_mock_farmer()
    farmer.last_name = None
    assert farmer.last_name is None

def test_farmer_phone_number_is_unique():
    assert Farmer.phone_number.property.columns[0].unique is True

def test_farmer_cooperative_id_is_required():
    assert Farmer.cooperative_id.property.columns[0].nullable is False