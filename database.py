import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured in .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def commit_session(db):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def add_record(db, model, data: dict):
    record = model(**data)
    db.add(record)
    db.flush()
    return record


def get_record(db, model, record_id):
    return db.get(model, record_id)


def update_record(db, record, data: dict):
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    return record


def delete_record(db, record):
    db.delete(record)
    db.flush()
