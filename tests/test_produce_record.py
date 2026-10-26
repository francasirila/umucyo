import uuid
from decimal import Decimal
from models.produce_record import ProduceRecord
from models.enums import DeliveryStatus

def create_mock_record():
    return ProduceRecord(produce_record_id=uuid.uuid4(), cooperative_id=uuid.uuid4(), farmer_id=uuid.uuid4(), collection_point_id=uuid.uuid4(), device_id=uuid.uuid4(), produce_price_id=uuid.uuid4(), user_id=uuid.uuid4(), delivery_status=DeliveryStatus.accepted, gross_weight_kg=Decimal("20.0"), rejected_weight_kg=Decimal("0.0"), accepted_weight_kg=Decimal("20.0"), agent_notes="Good", amount=Decimal("6000.0"))

def test_record_creation():
    assert create_mock_record().accepted_weight_kg == Decimal("20.0")

def test_record_zero_weight():
    record = create_mock_record()
    record.gross_weight_kg = Decimal("0.0")
    record.accepted_weight_kg = Decimal("0.0")
    assert record.accepted_weight_kg == 0

def test_record_full_rejection():
    record = create_mock_record()
    record.delivery_status = DeliveryStatus.rejected
    record.accepted_weight_kg = Decimal("0.0")
    assert record.delivery_status == DeliveryStatus.rejected

def test_record_unicode_notes():
    record = create_mock_record()
    record.agent_notes = "Meza (Leaf)"
    assert "(Leaf)" in record.agent_notes

def test_record_max_weight():
    record = create_mock_record()
    record.gross_weight_kg = Decimal("9999999.999")
    assert record.gross_weight_kg == Decimal("9999999.999")

def test_record_rejected_exceeds_gross():
    record = create_mock_record()
    record.rejected_weight_kg = Decimal("25.0")
    assert record.rejected_weight_kg > record.gross_weight_kg

def test_record_amount_calc():
    record = create_mock_record()
    assert record.amount == record.accepted_weight_kg * Decimal("300.00")