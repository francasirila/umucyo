import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers
from models import Base


@pytest.fixture(scope="session")
def engine():
    configure_mappers()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()
