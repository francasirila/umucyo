from models.cooperative_user import CooperativeUser
from models.farmer import Farmer
from models.user import User


def test_agent_inherits_user():
    assert issubclass(CooperativeUser, User)
    assert CooperativeUser.__table__.c.user_id.foreign_keys


def test_farmer_inherits_user():
    assert issubclass(Farmer, User)
    assert Farmer.__table__.c.user_id.foreign_keys


def test_user_has_polymorphic_discriminator():
    assert "user_type" in User.__mapper__.polymorphic_on.key
