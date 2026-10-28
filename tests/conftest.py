import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from routers.produce_record import router

from database import Base, get_db
from models import (
    CollectionPoint,
    Cooperative,
    CooperativeUser,
    Farmer,
    ProducePrice,
    ProduceRecord,
    WeighingDevice,
)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()




def _make_cooperative(db_session, **overrides) -> Cooperative:
    cooperative = Cooperative(
        **{
            "cooperative_name": "Umucyo Test Cooperative",
            "location": "Huye, Rwanda",
            "email": "coop@test.rw",
            **overrides,
        }
    )
    db_session.add(cooperative)
    db_session.commit()
    db_session.refresh(cooperative)
    return cooperative


def _make_collection_point(db_session, cooperative, **overrides) -> CollectionPoint:
    collection_point = CollectionPoint(
        **{
            "cooperative_id": cooperative.cooperative_id,
            "collection_name": "Main Collection Point",
            **overrides,
        }
    )
    db_session.add(collection_point)
    db_session.commit()
    db_session.refresh(collection_point)
    return collection_point


def _make_agent(db_session, cooperative, **overrides) -> CooperativeUser:
    agent = CooperativeUser(
        **{
            "first_name": "Alice",
            "last_name": "Uwase",
            "password_hash": "test-hash",
            "email": "alice@test.rw",
            "cooperative_id": cooperative.cooperative_id,
            **overrides,
        }
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def _make_farmer(db_session, collection_point, registered_by, **overrides) -> Farmer:
    farmer = Farmer(
        **{
            "farmer_id": uuid.uuid4(),
            "first_name": "Jean",
            "last_name": "Nkusi",
            "collection_point_id": collection_point.collection_point_id,
            "registered_by_user_id": registered_by.user_id,
            "phone_number": "+250788000002",
            **overrides,
        }
    )
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)
    return farmer


def _make_device(db_session, collection_point, **overrides) -> WeighingDevice:
    device = WeighingDevice(
        **{
            "collection_point_id": collection_point.collection_point_id,
            "serial_number": "UMC-DEV-TEST",
            **overrides,
        }
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


def _make_price(db_session, cooperative, created_by, **overrides) -> ProducePrice:
    price = ProducePrice(
        **{
            "cooperative_id": cooperative.cooperative_id,
            "unit": "kg",
            "price_per_unit": 350,
            "effective_from": datetime.now(timezone.utc),
            "created_by_user_id": created_by.user_id,
            **overrides,
        }
    )
    db_session.add(price)
    db_session.commit()
    db_session.refresh(price)
    return price


def build_graph(db_session) -> SimpleNamespace:
    cooperative = _make_cooperative(db_session)
    collection_point = _make_collection_point(db_session, cooperative)
    agent = _make_agent(db_session, cooperative)
    farmer = _make_farmer(db_session, collection_point, agent)
    device = _make_device(db_session, collection_point)
    price = _make_price(db_session, cooperative, agent)
    return SimpleNamespace(
        db=db_session,
        cooperative=cooperative,
        collection_point=collection_point,
        agent=agent,
        farmer=farmer,
        device=device,
        price=price,
    )


@pytest.fixture()
def produce_graph(db_session) -> SimpleNamespace:
    return build_graph(db_session)


def make_produce_record(graph: SimpleNamespace, **overrides) -> ProduceRecord:
    record = ProduceRecord(
        **{
            "cooperative_id": graph.cooperative.cooperative_id,
            "produce_price_id": graph.price.produce_price_id,
            "farmer_id": graph.farmer.user_id,
            "device_id": graph.device.device_id,
            "collection_point_id": graph.collection_point.collection_point_id,
            "delivery_status": "accepted",
            "user_id": graph.agent.user_id,
            "gross_weight_kg": 75.5,
            "agent_notes": "Clean coffee cherries",
            "amount": 26425.00,
            **overrides,
        }
    )
    graph.db.add(record)
    graph.db.commit()
    graph.db.refresh(record)
    return record


def produce_record_payload(graph: SimpleNamespace, **overrides) -> dict:
    payload = {
        "cooperative_id": str(graph.cooperative.cooperative_id),
        "produce_price_id": str(graph.price.produce_price_id),
        "farmer_id": str(graph.farmer.user_id),
        "device_id": str(graph.device.device_id),
        "collection_point_id": str(graph.collection_point.collection_point_id),
        "delivery_status": "accepted",
        "user_id": str(graph.agent.user_id),
        "gross_weight_kg": "75.500",
        "agent_notes": "Clean coffee cherries",
        **overrides,
    }
    return payload


@pytest.fixture()
def api_client(db_session):
    from routers.produce_record import router

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
