from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.auth import CooperativeRegistration, SetPasswordRequest, VerifyOTPRequest
from schemas.collection_point import CollectionPointCreate, CollectionPointUpdate
from schemas.users import AdminCreate, AgentCreate, AgentUpdate, FarmerCreate


def farmer(**overrides):
    data = {
        "first_name": "A",
        "last_name": "B",
        "phone_number": "+250788123456",
        "id_number": "RW-12345",
        "collection_point_id": uuid4(),
    }
    data.update(overrides)
    return FarmerCreate(**data)


def test_valid_farmer_payload():
    assert farmer().phone_number == "+250788123456"


@pytest.mark.parametrize("phone", ["0788123456", "+0788123456", "+25", "250788123456", "+250 788 123 456"])
def test_invalid_phone_numbers(phone):
    with pytest.raises(ValidationError):
        farmer(phone_number=phone)


@pytest.mark.parametrize("code", ["12345", "1234567", "12345a", ""])
def test_otp_code_must_be_six_digits(code):
    with pytest.raises(ValidationError):
        VerifyOTPRequest(email="a@example.com", code=code)


def test_set_password_requires_long_token_and_password():
    with pytest.raises(ValidationError):
        SetPasswordRequest(token="short", password="SecurePassword123")
    with pytest.raises(ValidationError):
        SetPasswordRequest(token="x" * 30, password="short")


def test_cooperative_registration_validates_email_and_lengths():
    base = {
        "cooperative_name": "Coop",
        "email": "a@example.com",
        "first_name": "A",
        "last_name": "B",
        "password": "SecurePassword123",
    }
    assert CooperativeRegistration(**base)
    for field, value in [("email", "nope"), ("cooperative_name", "A"), ("password", "short")]:
        with pytest.raises(ValidationError):
            CooperativeRegistration(**{**base, field: value})


def test_admin_and_agent_create_require_valid_email():
    with pytest.raises(ValidationError):
        AdminCreate(first_name="A", last_name="B", email="bad", password="SecurePassword123")
    with pytest.raises(ValidationError):
        AgentCreate(first_name="A", last_name="B", email="bad", collection_point_id=uuid4())


def test_agent_update_is_fully_optional_and_validates_status():
    assert AgentUpdate().model_dump(exclude_unset=True) == {}
    assert AgentUpdate(status="inactive").status.value == "inactive"
    with pytest.raises(ValidationError):
        AgentUpdate(status="deleted")


def test_collection_point_schemas():
    assert CollectionPointCreate(collection_name="Ab").collection_name == "Ab"
    with pytest.raises(ValidationError):
        CollectionPointCreate(collection_name="A")
    assert CollectionPointUpdate().model_dump(exclude_unset=True) == {}
