import uuid
from datetime import datetime
from decimal import Decimal
from models.produce_price import ProducePrice

def create_mock_price():
    return ProducePrice(produce_price_id=uuid.uuid4(), cooperative_id=uuid.uuid4(), unit="kg", price_per_unit=Decimal("300.50"), effective_from=datetime.now(), created_by_user_id=uuid.uuid4())

def test_price_creation():
    assert create_mock_price().price_per_unit == Decimal("300.50")

def test_price_negative():
    price = create_mock_price()
    price.price_per_unit = Decimal("-10.00")
    assert price.price_per_unit < 0

def test_price_zero():
    price = create_mock_price()
    price.price_per_unit = Decimal("0.00")
    assert price.price_per_unit == 0

def test_price_future_date():
    price = create_mock_price()
    price.effective_from = datetime(2030, 1, 1)
    assert price.effective_from.year == 2030

def test_price_max_decimal():
    price = create_mock_price()
    price.price_per_unit = Decimal("9999999999.99")
    assert price.price_per_unit == Decimal("9999999999.99")

def test_price_kg_unit():
    assert create_mock_price().unit == "kg"

def test_price_missing_effective_to():
    price = create_mock_price()
    price.effective_to = None
    assert price.effective_to is None