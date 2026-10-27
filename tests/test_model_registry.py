import pytest
from sqlalchemy.orm import configure_mappers
from models import (
    Base,
    User,
    CollectionPoint,
    AgentAssignment,
    WeighingDevice,
    ProduceRecord,
    ProducePrice,
    PaymentTransaction,
    Task,
    AuditLog,
    MessageLog,
)

MODEL_TABLES = [
    (User, "users"),
    (CollectionPoint, "collection_point"),
    (AgentAssignment, "agent_assignment"),
    (WeighingDevice, "weighing_device"),
    (ProduceRecord, "produce_record"),
    (ProducePrice, "produce_price"),
    (PaymentTransaction, "payment_transaction"),
    (Task, "task"),
    (AuditLog, "audit_log"),
    (MessageLog, "message_log"),
]


@pytest.mark.parametrize("model,table_name", MODEL_TABLES)
def test_model_is_registered(model, table_name):
    assert Base.metadata.tables[table_name] is model.__table__


@pytest.mark.parametrize("model,table_name", MODEL_TABLES)
def test_table_has_primary_key(model, table_name):
    assert len(model.__table__.primary_key.columns) == 1


def test_mappers_configure_without_errors():
    configure_mappers()


def test_only_merged_user_model_represents_cooperative_and_farmer_records():
    assert "users" in Base.metadata.tables
    assert "cooperative" not in Base.metadata.tables
    assert "farmer" not in Base.metadata.tables
    assert not hasattr(__import__("models", fromlist=["*"]), "Cooperative")
    assert not hasattr(__import__("models", fromlist=["*"]), "Farmer")


def test_removed_cooperative_id_is_not_present_on_any_table():
    assert all(("cooperative_id" not in table.columns for table in Base.metadata.tables.values()))


@pytest.mark.parametrize("model,table_name", MODEL_TABLES)
def test_registered_model_has_columns(model, table_name):
    assert len(model.__table__.columns) > 1


@pytest.mark.parametrize("model,table_name", MODEL_TABLES)
def test_registered_model_has_mapper(model, table_name):
    assert model.__mapper__.class_ is model
