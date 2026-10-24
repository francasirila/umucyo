import uuid
from decimal import Decimal

from models.cooperative import Cooperative
from models.enums import (
    AccountStatus,
    CooperativeStatus,
    DeliveryStatus,
)
from models.farmer import Farmer
from models.produce_record import ProduceRecord


def test_cooperative_model_creation():
    """Test that a Cooperative instance can be created with correct attributes."""
    test_id = uuid.uuid4()
    coop = Cooperative(
        cooperative_id=test_id,
        cooperative_name="Kigali Tea Cooperative",
        location="Kigali",
        phone_number="0788000000",
        email="info@kigalitea.rw",
        status=CooperativeStatus.active,
    )

    assert coop.cooperative_id == test_id
    assert coop.cooperative_name == "Kigali Tea Cooperative"
    assert coop.status == CooperativeStatus.active


def test_farmer_model_creation():
    """Test that a Farmer instance can be created and defaults are applied."""
    farmer_id = uuid.uuid4()
    coop_id = uuid.uuid4()
    collection_point_id = uuid.uuid4()
    agent_id = uuid.uuid4()

    farmer = Farmer(
        farmer_id=farmer_id,
        cooperative_id=coop_id,
        collection_point_id=collection_point_id,
        first_name="Jean",
        last_name="Claude",
        phone_number="0788111222",
        registered_by_user_id=agent_id,
        status=AccountStatus.active,  # Explicitly set for the in-memory test
    )

    assert farmer.farmer_id == farmer_id
    assert farmer.first_name == "Jean"
    assert farmer.last_name == "Claude"
    assert farmer.status == AccountStatus.active


def test_produce_record_relationships():
    """Test that a ProduceRecord has the correct foreign keys."""
    record_id = uuid.uuid4()
    coop_id = uuid.uuid4()

    record = ProduceRecord(
        produce_record_id=record_id,
        cooperative_id=coop_id,
        farmer_id=uuid.uuid4(),
        collection_point_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        produce_price_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        delivery_status=DeliveryStatus.accepted,
        gross_weight_kg=Decimal("15.500"),
        rejected_weight_kg=Decimal("0.000"),
        accepted_weight_kg=Decimal("15.500"),
        agent_notes="Leaf looks good.",
        amount=Decimal("4500.00"),
    )

    assert record.produce_record_id == record_id
    assert record.gross_weight_kg == Decimal("15.500")
    assert record.delivery_status == DeliveryStatus.accepted
