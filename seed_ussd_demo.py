"""Local demo data for the USSD flow. MOCK FILE: do not commit it.

    DEMO_PHONE=0788123456 python3 seed_ussd_demo.py
    python3 seed_ussd_demo.py --schema   # print the columns of every table
    python3 seed_ussd_demo.py --force    # allow a database whose name has no "local" in it

It refuses to run on a database whose name does not contain "local", so it cannot
touch a shared database by accident.
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import inspect as sa_inspect

import models  # noqa: F401  (registers every model with SQLAlchemy)
from database import Base, engine, get_db
from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.enums import (
    AccountStatus,
    CooperativeStatus,
    DeliveryStatus,
    PaymentStatus,
    UserType,
)
from models.farmer import Farmer
from models.payment_transaction import PaymentTransaction
from models.produce_price import ProducePrice
from models.produce_record import ProduceRecord

PHONE = os.getenv("DEMO_PHONE", "0788123456")


# ---------------------------------------------------------------- helpers
def _attrs(Model):
    """Mapped attribute name -> Column, including columns inherited from a parent table."""
    return {a.key: a.columns[0] for a in sa_inspect(Model).column_attrs}


def _only(Model, **values):
    """Keep only the values the model really has, and say which ones were dropped."""
    attrs = _attrs(Model)
    ignored = [k for k in values if k not in attrs]
    if ignored:
        print(f"  {Model.__name__}: ignoring {ignored}")
    return {k: v for k, v in values.items() if k in attrs}


def _model_for_table(table_name):
    return next(m.class_ for m in Base.registry.mappers if m.local_table.name == table_name)


def _make(Model, **known):
    """Build a Model from `known` values, filling any other required column with a dummy value."""
    attrs = _attrs(Model)
    values = {k: v for k, v in known.items() if k in attrs}
    for key, col in attrs.items():
        if key in values or col.nullable or col.default is not None or col.server_default is not None:
            continue
        t = col.type
        if isinstance(t, SAEnum):
            values[key] = list(t.enum_class)[0] if t.enum_class else t.enums[0]
            continue
        try:
            py = t.python_type
        except NotImplementedError:
            py = None
        if py is uuid.UUID and col.primary_key:
            values[key] = uuid.uuid4()
        elif py is bool:
            values[key] = False
        elif py is str:
            values[key] = f"demo-{key}"
        elif py in (int, float, Decimal):
            values[key] = py(0)
        elif py is datetime:
            values[key] = datetime.now(timezone.utc)
        elif py is date:
            values[key] = date.today()
        else:
            raise RuntimeError(f"Set {Model.__name__}.{key} by hand in seed_ussd_demo.py")
    return Model(**values)


def _check_database():
    name = engine.url.database or ""
    if "local" not in name and "--force" not in sys.argv:
        sys.exit(
            f"Refusing to seed database '{name}' (name does not contain 'local').\n"
            "Point DATABASE_URL in .env at your private database, or pass --force."
        )


def show_schema():
    for name, table in sorted(Base.metadata.tables.items()):
        print(f"\n{name}")
        for col in table.columns:
            flags = []
            if col.primary_key:
                flags.append("pk")
            if not col.nullable:
                flags.append("required")
            print(f"  {col.name:28} {str(col.type):22} {' '.join(flags)}")


# ------------------------------------------------------------------- seed
def seed():
    _check_database()
    print(f"database           = {engine.url.database}")
    db = next(get_db())
    try:
        # cooperative
        coop = db.query(Cooperative).filter(Cooperative.cooperative_name == "Demo Cooperative").first()
        if not coop:
            coop = Cooperative(
                **_only(
                    Cooperative,
                    cooperative_id=uuid.uuid4(),
                    cooperative_name="Demo Cooperative",
                    location="Kigali",
                    email="demo@coop.rw",
                    status=CooperativeStatus.active,
                )
            )
            db.add(coop)
            db.flush()
        print(f"cooperative        = {coop.cooperative_id}")

        # collection point
        cp = (
            db.query(CollectionPoint)
            .filter(
                CollectionPoint.cooperative_id == coop.cooperative_id,
                CollectionPoint.collection_name == "Main",
            )
            .first()
        )
        if not cp:
            cp = CollectionPoint(
                **_only(
                    CollectionPoint,
                    collection_point_id=uuid.uuid4(),
                    cooperative_id=coop.cooperative_id,
                    collection_name="Main",
                    status=AccountStatus.active,
                )
            )
            db.add(cp)
            db.flush()
        print(f"collection_point   = {cp.collection_point_id}")

        # agent
        agent = db.query(CooperativeUser).filter(CooperativeUser.email == "agent@coop.rw").first()
        if not agent:
            agent = CooperativeUser(
                **_only(
                    CooperativeUser,
                    user_id=uuid.uuid4(),
                    first_name="Demo",
                    last_name="Agent",
                    status=AccountStatus.active,
                    user_type=UserType.cooperative_agent,
                    password_hash="demo",
                    email="agent@coop.rw",
                    cooperative_id=coop.cooperative_id,
                )
            )
            db.add(agent)
            db.flush()
        print(f"cooperative_user   = {agent.user_id}")

        # farmer (this is the registered phone number USSD looks up)
        farmer = db.query(Farmer).filter(Farmer.phone_number.like(f"%{PHONE[-9:]}")).first()
        if not farmer:
            farmer = Farmer(
                **_only(
                    Farmer,
                    farmer_id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    first_name="Demo",
                    last_name="Farmer",
                    status=AccountStatus.active,
                    user_type=UserType.farmer,
                    cooperative_id=coop.cooperative_id,
                    collection_point_id=cp.collection_point_id,
                    registered_by_user_id=agent.user_id,
                    phone_number=PHONE,
                )
            )
            db.add(farmer)
            db.flush()
        print(f"farmer             = {farmer.user_id}  ({farmer.phone_number})")

        # price
        price = db.query(ProducePrice).filter(ProducePrice.cooperative_id == coop.cooperative_id).first()
        if not price:
            price = ProducePrice(
                **_only(
                    ProducePrice,
                    cooperative_id=coop.cooperative_id,
                    unit="kg",
                    price_per_unit=Decimal("300.00"),
                    effective_from=datetime(2025, 1, 1),
                    created_by_user_id=agent.user_id,
                )
            )
            db.add(price)
            db.flush()

        # delivery + payment (a payment needs a produce record, which needs a weighing device)
        has_payment = (
            db.query(PaymentTransaction).filter(PaymentTransaction.farmer_id == farmer.user_id).first()
        )
        if has_payment:
            print("payment_transaction = already present")
        else:
            device = _make(
                _model_for_table("weighing_device"),
                device_id=uuid.uuid4(),
                cooperative_id=coop.cooperative_id,
                collection_point_id=cp.collection_point_id,
                user_id=agent.user_id,
                registered_by_user_id=agent.user_id,
            )
            db.add(device)
            db.flush()

            # dated last month, so "last 3 months" always has data whatever today's date is
            last_month = date.today().replace(day=1) - timedelta(days=1)
            record = ProduceRecord(
                produce_record_id=uuid.uuid4(),
                cooperative_id=coop.cooperative_id,
                produce_price_id=price.produce_price_id,
                farmer_id=farmer.user_id,
                device_id=device.device_id,
                collection_point_id=cp.collection_point_id,
                delivery_status=DeliveryStatus.accepted,
                user_id=agent.user_id,
                gross_weight_kg=Decimal("100.000"),
                agent_notes="demo",
                amount=Decimal("30000.00"),
                recorded_at=datetime(last_month.year, last_month.month, 15, 10, 0, tzinfo=timezone.utc),
            )
            db.add(record)
            db.flush()

            db.add(
                PaymentTransaction(
                    **_only(
                        PaymentTransaction,
                        farmer_id=farmer.user_id,
                        user_id=agent.user_id,
                        produce_price_id=price.produce_price_id,
                        produce_record_id=record.produce_record_id,
                        provider="MTN MoMo",
                        quantity=Decimal("100.000"),
                        amount=Decimal("30000.00"),
                        transaction_reference=f"DEMO-{uuid.uuid4().hex[:8]}",
                        status=PaymentStatus.paid,
                        failure_reason="none",  # model requires a value even for paid rows
                        approved_at=datetime(last_month.year, last_month.month, 19, 10, 0, tzinfo=timezone.utc),
                        approved_by=agent.user_id,
                        payment_date=datetime(last_month.year, last_month.month, 20, 10, 0, tzinfo=timezone.utc),
                    )
                )
            )
            print(f"payment_transaction = 1 added ({last_month:%b %Y}, 100kg, paid)")

        db.commit()
        print(f"\nOK. In Postman use phoneNumber={PHONE} (or +250{PHONE[-9:]}). cooperative_id={coop.cooperative_id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if "--schema" in sys.argv:
        show_schema()
    else:
        seed()