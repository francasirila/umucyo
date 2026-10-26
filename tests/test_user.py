import uuid
from models.user import User
from models.enums import UserRole, AccountStatus


def create_mock_user():
    return User(
        user_id=uuid.uuid4(),
        cooperative_id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        role=UserRole.agent,
        password_hash="hash",
        email="a@b.c",
        status=AccountStatus.active,
    )


def test_user_creation():
    assert create_mock_user().first_name == "John"


def test_user_admin_role():
    user = create_mock_user()
    user.role = UserRole.admin
    assert user.role == UserRole.admin


def test_user_invalid_role():
    user = create_mock_user()
    user.role = "superadmin"
    assert user.role == "superadmin"


def test_user_empty_password():
    user = create_mock_user()
    user.password_hash = ""
    assert user.password_hash == ""


def test_user_long_password():
    user = create_mock_user()
    user.password_hash = "A" * 255
    assert len(user.password_hash) == 255


def test_user_inactive_status():
    user = create_mock_user()
    user.status = AccountStatus.inactive
    assert user.status == AccountStatus.inactive
