from models.weighing_device import WeighingDevice


def test_weighing_device_table_name():
    assert WeighingDevice.__tablename__ == "weighing_device"


def test_weighing_device_has_expected_columns():
    expected = ["device_id", "collection_point_id", "serial_number", "status", "registered_at"]
    assert expected == [column.name for column in WeighingDevice.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(WeighingDevice.__table__.columns.keys()))


def test_weighing_device_has_primary_key():
    assert WeighingDevice.__table__.primary_key.columns
