import pytest
from models import WeighingDevice, DeviceStatus
from tests.helpers import (
    column,
    constraint_names,
    foreign_key_targets,
    relationship_names,
)


@pytest.mark.parametrize(
    "name",
    ["device_id", "collection_point_id", "serial_number", "status", "registered_at"],
)
def test_device_columns_exist(name):
    assert name in WeighingDevice.__table__.columns


@pytest.mark.parametrize(
    "name",
    ["device_id", "collection_point_id", "serial_number", "status", "registered_at"],
)
def test_device_required_columns(name):
    assert column(WeighingDevice, name).nullable is False


def test_device_collection_point_foreign_key():
    assert foreign_key_targets(WeighingDevice, "collection_point_id") == {"collection_point.collection_point_id"}


def test_device_serial_number_is_unique():
    assert "uq_weighing_device_serial" in constraint_names(WeighingDevice)


def test_device_default_status():
    assert WeighingDevice.status.default.arg == DeviceStatus.ACTIVE


@pytest.mark.parametrize("name", ["collection_point", "produce_records"])
def test_device_relationships(name):
    assert name in relationship_names(WeighingDevice)
