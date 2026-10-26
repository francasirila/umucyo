import uuid
from models.weighing_device import WeighingDevice
from models.enums import DeviceStatus

def create_mock_device():
    return WeighingDevice(device_id=uuid.uuid4(), collection_point_id=uuid.uuid4(), serial_number="SN-1", status=DeviceStatus.active)

def test_device_creation():
    assert create_mock_device().serial_number == "SN-1"

def test_device_inactive():
    device = create_mock_device()
    device.status = DeviceStatus.inactive
    assert device.status == DeviceStatus.inactive

def test_device_long_serial():
    device = create_mock_device()
    device.serial_number = "A" * 100
    assert len(device.serial_number) == 100

def test_device_empty_serial():
    device = create_mock_device()
    device.serial_number = ""
    assert device.serial_number == ""

def test_device_special_serial():
    device = create_mock_device()
    device.serial_number = "SN-#123/X"
    assert "#" in device.serial_number