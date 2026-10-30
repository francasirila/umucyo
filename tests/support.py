"""Shared test setup: an in-memory database and a small world that matches develop's models."""

import uuid
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (registers every table)
from database import Base
from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.enums import AccountStatus, CooperativeStatus, DeliveryStatus, UserType
from models.farmer import Farmer
from models.produce_price import ProducePrice
from models.produce_record import ProduceRecord
from models.weighing_device import WeighingDevice

FARMER_PHONE = "0788123456"
OTHER_FARMER_PHONE = "0788999888"


def make_session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False), engine


def _cooperative(db, name, email):
    ids = SimpleNamespace(
        coop=uuid.uuid4(), point=uuid.uuid4(), agent=uuid.uuid4(), farmer=uuid.uuid4()
    )
    db.add(
        Cooperative(
            cooperative_id=ids.coop,
            cooperative_name=name,
            location="Kigali",
            email=email,
            status=CooperativeStatus.active,
        )
    )
    db.flush()
    db.add(
        CollectionPoint(
            collection_point_id=ids.point,
            cooperative_id=ids.coop,
            collection_name="Main",
            status=AccountStatus.active,
        )
    )
    db.flush()
    db.add(
        CooperativeUser(
            user_id=ids.agent,
            first_name="Agent",
            last_name="Smith",
            email=f"agent-{ids.agent}@test.com",
            password_hash="hash",
            cooperative_id=ids.coop,
            user_type=UserType.cooperative_agent,
        )
    )
    db.flush()
    return ids


def _farmer(db, ids, first, last, phone):
    db.add(
        Farmer(
            user_id=ids.farmer,
            farmer_id=uuid.uuid4(),
            first_name=first,
            last_name=last,
            phone_number=phone,
            collection_point_id=ids.point,
            registered_by_user_id=ids.agent,
            user_type=UserType.farmer,
        )
    )
    db.flush()


def seed_world(db):
    """Two cooperatives, each with a collection point, an agent and a farmer."""
    mine = _cooperative(db, "Test Coop", "test@test.com")
    _farmer(db, mine, "John", "Doe", FARMER_PHONE)
    other = _cooperative(db, "Other Coop", "other@test.com")
    _farmer(db, other, "Jane", "Roe", OTHER_FARMER_PHONE)

    device, price = uuid.uuid4(), uuid.uuid4()
    db.add(
        WeighingDevice(
            device_id=device,
            collection_point_id=mine.point,
            serial_number="SN-1",
            status=AccountStatus.active,
        )
    )
    db.flush()
    db.add(
        ProducePrice(
            produce_price_id=price,
            cooperative_id=mine.coop,
            unit="kg",
            price_per_unit=100,
            effective_from=_now(),
            created_by_user_id=mine.agent,
        )
    )
    db.flush()
    db.commit()
    return SimpleNamespace(mine=mine, other=other, device=device, price=price)


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def add_produce_record(db, world, **overrides):
    """A delivery of 100 kg by John, recorded on 28 Oct 2026."""
    from datetime import datetime, timezone

    data = {
        "produce_record_id": uuid.uuid4(),
        "cooperative_id": world.mine.coop,
        "produce_price_id": world.price,
        "farmer_id": world.mine.farmer,
        "device_id": world.device,
        "collection_point_id": world.mine.point,
        "delivery_status": DeliveryStatus.accepted,
        "user_id": world.mine.agent,
        "gross_weight_kg": 100,
        "agent_notes": "Good",
        "amount": 9500,
        "recorded_at": datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc),
    }
    data.update(overrides)
    record = ProduceRecord(**data)
    db.add(record)
    db.commit()
    return record
