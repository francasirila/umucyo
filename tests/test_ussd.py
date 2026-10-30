"""All USSD tests: menus, language, payment history, reporting, robustness."""

from models.enums import CooperativeStatus
import types
import uuid
from datetime import date, datetime, time, timezone
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base, get_db
from main import app
from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeUser
from models.enums import AccountStatus, DeliveryStatus, PaymentStatus, UserType
from models.farmer import Farmer
from models.payment_transaction import PaymentTransaction
from models.produce_price import ProducePrice
from models.produce_record import ProduceRecord
from models.weighing_device import WeighingDevice
from services.sms_service import SmsService
import logging
from services.translations import LANGUAGE_MENU, format_date, month_label
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock
import services.ussd_service as ussd_module
from models.task import Task
from services.ussd_service import UssdService
import sys
from models.payment_report import PaymentReport
import string
from services.translations import (
    BILINGUAL,
    DEFAULT_LANGUAGE,
    LANGUAGES,
    MONTHS,
    STRINGS,
    tr,
)


FARMER_PHONE = "0788123456"


FARMER_NO_PAYMENTS_PHONE = "0788999888"


def month_start(offset: int) -> date:
    """First day of the month `offset` months ago (0 = this month)."""
    today = date.today()
    year, month = today.year, today.month - offset
    while month < 1:
        month += 12
        year -= 1
    return date(year, month, 1)


@pytest.fixture(autouse=True)
def no_real_sms_credentials(monkeypatch):
    """Make sure no test can ever call the real Africa's Talking API by accident."""
    monkeypatch.delenv("AT_USERNAME", raising=False)
    monkeypatch.delenv("AT_API_KEY", raising=False)


@pytest.fixture()
def api_session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def api_db(api_session_factory):
    session = api_session_factory()
    yield session
    session.close()


@pytest.fixture()
def api_client(api_session_factory):
    """TestClient wired to the in-memory database. No lifespan, so the real database is never touched."""

    def override_get_db():
        session = api_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(api_db):
    """Cooperative, point, agent, two farmers, and 3 months of payments for John."""
    ids = SimpleNamespace(
        coop=uuid.uuid4(),
        point=uuid.uuid4(),
        agent=uuid.uuid4(),
        farmer=uuid.uuid4(),
        farmer2=uuid.uuid4(),
        device=uuid.uuid4(),
        price=uuid.uuid4(),
        record=uuid.uuid4(),
    )
    db = api_db
    db.add(
        Cooperative(
            cooperative_id=ids.coop,
            cooperative_name="Test Coop",
            location="Kigali",
            email="test@test.com",
            status=CooperativeStatus.active,
        )
    )
    db.flush()
    db.add(
        CollectionPoint(
            collection_point_id=ids.point,
            cooperative_id=ids.coop,
            collection_name="Main",
            status=AccountStatus.active,
        )
    )
    db.flush()
    db.add(
        CooperativeUser(
            user_id=ids.agent,
            first_name="Agent",
            last_name="Smith",
            email="agent@test.com",
            password_hash="hash",
            cooperative_id=ids.coop,
            user_type=UserType.cooperative_agent,
        )
    )
    db.flush()
    for farmer_id, first, last, phone in (
        (ids.farmer, "John", "Doe", FARMER_PHONE),
        (ids.farmer2, "Jane", "Roe", FARMER_NO_PAYMENTS_PHONE),
    ):
        db.add(
            Farmer(
                user_id=farmer_id,
                farmer_id=uuid.uuid4(),
                first_name=first,
                last_name=last,
                phone_number=phone,
                collection_point_id=ids.point,
                registered_by_user_id=ids.agent,
                user_type=UserType.farmer,
            )
        )
    db.flush()
    db.add(
        WeighingDevice(
            device_id=ids.device,
            collection_point_id=ids.point,
            serial_number="SN-1",
            status=AccountStatus.active,
        )
    )
    db.flush()
    db.add(
        ProducePrice(
            produce_price_id=ids.price,
            cooperative_id=ids.coop,
            unit="kg",
            price_per_unit=100.0,
            effective_from=datetime.now(timezone.utc),
            created_by_user_id=ids.agent,
        )
    )
    db.flush()
    db.add(
        ProduceRecord(
            produce_record_id=ids.record,
            cooperative_id=ids.coop,
            produce_price_id=ids.price,
            farmer_id=ids.farmer,
            device_id=ids.device,
            collection_point_id=ids.point,
            delivery_status=DeliveryStatus.accepted,
            user_id=ids.agent,
            gross_weight_kg=100,
            agent_notes="Good",
            amount=9500,
        )
    )
    db.flush()

    # offset 0 = this month (paid), 1 = last month (unpaid), 2 = two months ago (paid)
    ids.paid_on = datetime.combine(date.today(), time(12, 0), tzinfo=timezone.utc)
    for offset, status in (
        (0, PaymentStatus.paid),
        (1, PaymentStatus.pending),
        (2, PaymentStatus.paid),
    ):
        start = month_start(offset)
        delivered = datetime(start.year, start.month, 5, 12, 0, tzinfo=timezone.utc)
        record_id = uuid.uuid4()
        db.add(
            ProduceRecord(
                produce_record_id=record_id,
                cooperative_id=ids.coop,
                produce_price_id=ids.price,
                farmer_id=ids.farmer,
                device_id=ids.device,
                collection_point_id=ids.point,
                delivery_status=DeliveryStatus.accepted,
                user_id=ids.agent,
                gross_weight_kg=100,
                amount=9500,
                recorded_at=delivered,
            )
        )
        db.flush()
        db.add(
            PaymentTransaction(
                farmer_id=ids.farmer,
                user_id=ids.agent,
                produce_price_id=ids.price,
                produce_record_id=record_id,
                quantity=100,
                amount=9500,
                transaction_reference=f"TEST-{start.isoformat()}-{uuid.uuid4().hex[:6]}",
                failure_reason="",
                status=status,
                approved_at=ids.paid_on,
                payment_date=ids.paid_on,
            )
        )
    db.commit()
    return ids


@pytest.fixture()
def outbox(monkeypatch):
    """Replaces the SMS provider with a recorder. Each item is (phone_number, message)."""
    sent: list[tuple[str, str]] = []

    def fake_send(self, phone_number, message):
        sent.append((phone_number, message))
        return True

    monkeypatch.setattr(SmsService, "send_custom_sms", fake_send)
    return sent


def make_fake_africastalking(status: str = "Success") -> types.ModuleType:
    """A stand-in for the `africastalking` SDK. It records calls and never touches the network."""
    module = types.ModuleType("africastalking")
    module.calls = {"initialize": [], "send": []}

    def initialize(username, api_key):
        module.calls["initialize"].append((username, api_key))

    class SMS:
        @staticmethod
        def send(message, recipients):
            module.calls["send"].append((message, recipients))
            return {
                "SMSMessageData": {
                    "Recipients": [{"number": r, "status": status} for r in recipients]
                }
            }

    module.initialize = initialize
    module.SMS = SMS
    return module


URL = "/api/v1/ussd/"


def dial(client, text="", phone=FARMER_PHONE, lang="2"):
    """Dials as an English speaker by default: the first input is the language (1 = Kinyarwanda, 2 = English)."""
    full = f"{lang}*{text}" if text else lang
    return client.post(
        URL,
        data={
            "phoneNumber": phone,
            "sessionId": "s1",
            "serviceCode": "*384*123#",
            "text": full,
        },
    )


def test_reply_is_plain_text_not_json(api_client, seeded):
    response = dial(api_client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.startswith("CON ")


def test_main_menu_on_first_dial(api_client, seeded):
    body = dial(api_client).text
    assert "Payment History" in body
    assert "Report a Payment Issue" in body


def test_text_field_may_be_omitted(api_client, seeded):
    response = api_client.post(URL, data={"phoneNumber": FARMER_PHONE})
    assert response.status_code == 200
    assert response.text.startswith("CON ") and "Choose language" in response.text


@pytest.mark.parametrize("phone", ["0788123456", "250788123456", "+250788123456"])
def test_every_phone_format_finds_the_farmer(api_client, seeded, phone):
    assert dial(api_client, phone=phone).text.startswith("CON ")


def test_unregistered_phone(api_client, seeded):
    body = dial(api_client, phone="+250799999999").text
    assert body.startswith("END ") and "not registered" in body


def test_too_short_phone(api_client, seeded):
    reply = dial(api_client, phone="123").text
    assert reply.startswith("END Invalid phone number.") and "Numero ya telefone ntiyemewe" in reply


def test_invalid_main_choice(api_client, seeded):
    assert dial(api_client, "7").text.startswith("END Invalid choice")


def test_history_menu(api_client, seeded):
    body = dial(api_client, "1").text
    assert body.startswith("CON ")
    assert "This month" in body and "Last 3 months" in body


def test_history_this_month_shows_weight_and_paid_date(api_client, seeded):
    body = dial(api_client, "1*1").text
    assert body.startswith("END ")
    assert month_start(0).strftime("%b %Y") in body
    assert "100.0 kg" in body
    assert f"Paid on {date.today():%d %b %Y}" in body


def test_history_last_three_months(api_client, seeded):
    lines = dial(api_client, "1*2").text.split("\n")
    assert lines[0] == "END Last 3 months:"
    assert len(lines) == 4
    assert lines[1].startswith(month_start(2).strftime("%b")) and "Paid on" in lines[1]
    assert lines[2].startswith(month_start(1).strftime("%b")) and lines[2].endswith("Unpaid")
    assert lines[3].startswith(month_start(0).strftime("%b")) and "Paid on" in lines[3]
    assert all("100.0kg" in line for line in lines[1:])


def test_history_with_no_payments(api_client, seeded):
    body = dial(api_client, "1*1", phone=FARMER_NO_PAYMENTS_PHONE).text
    assert body == f"END {month_start(0).strftime('%b %Y')}: no records."
    assert dial(api_client, "1*2", phone=FARMER_NO_PAYMENTS_PHONE).text.count("no records") == 3


def test_history_invalid_choice(api_client, seeded):
    assert dial(api_client, "1*9").text.startswith("END Invalid choice")


def test_report_menu(api_client, seeded):
    body = dial(api_client, "2").text
    assert body.startswith("CON ")
    assert "Less payment" in body and "Not paid at all" in body


@pytest.mark.parametrize("text", ["2*1", "2*2"])
def test_report_asks_which_month(api_client, seeded, text):
    body = dial(api_client, text).text
    assert body.startswith("CON ") and "Which month" in body
    for offset in range(3):
        assert month_start(offset).strftime("%b %Y") in body


def test_less_payment_report_is_logged_and_farmer_gets_confirmation(
    api_client, seeded, outbox, caplog
):
    caplog.set_level(logging.INFO)
    body = dial(api_client, "2*1*2").text
    label = month_start(1).strftime("%b %Y")
    assert body == "END Your report was sent successfully."
    assert "LESS PAYMENT" in caplog.text and label in caplog.text and "John" in caplog.text
    assert len(outbox) == 1
    phone, text = outbox[0]
    assert phone == FARMER_PHONE
    assert "less payment" in text and label in text


def test_not_paid_report_is_logged_and_farmer_gets_confirmation(api_client, seeded, outbox, caplog):
    caplog.set_level(logging.INFO)
    body = dial(api_client, "2*2*1").text
    label = month_start(0).strftime("%b %Y")
    assert body == "END Your report was sent successfully."
    assert "NOT PAID AT ALL" in caplog.text and label in caplog.text
    assert [phone for phone, _ in outbox] == [FARMER_PHONE]
    assert "not paid" in outbox[0][1]


@pytest.mark.parametrize("text", ["2*1*9", "2*2*0", "2*2*abc"])
def test_report_invalid_month_sends_nothing(api_client, seeded, outbox, text):
    assert dial(api_client, text).text.startswith("END Invalid month")
    assert outbox == []


def test_report_invalid_kind(api_client, seeded, outbox):
    assert dial(api_client, "2*5").text.startswith("END Invalid choice")
    assert outbox == []


def test_report_fails_honestly_when_the_confirmation_sms_cannot_be_sent(
    api_client, seeded, monkeypatch
):
    monkeypatch.setattr(SmsService, "send_custom_sms", lambda self, phone, message: False)
    assert dial(api_client, "2*1*1").text.startswith("END Sorry, we could not send your report")


def test_report_fails_honestly_when_sms_provider_is_down(api_client, seeded, monkeypatch):
    def boom(self, phone_number, message):
        raise RuntimeError("gateway down")

    monkeypatch.setattr(SmsService, "send_custom_sms", boom)
    assert dial(api_client, "2*1*1").text.startswith("END Sorry, we could not send your report")


RW, EN = "1", "2"


def raw(client, text, phone=FARMER_PHONE):
    return client.post(URL, data={"phoneNumber": phone, "text": text}).text


def dial_ussd_language(client, text, lang):
    return raw(client, f"{lang}*{text}" if text else lang)


def test_the_first_dial_asks_for_the_language(api_client, seeded):
    assert raw(api_client, "") == LANGUAGE_MENU


def test_the_language_is_asked_every_time_nothing_is_remembered(api_client, seeded):
    dial_ussd_language(api_client, "1", RW)
    assert raw(api_client, "") == LANGUAGE_MENU


def test_choosing_kinyarwanda_shows_the_kinyarwanda_menu(api_client, seeded):
    reply = raw(api_client, RW)
    assert reply.startswith("CON Murakaza neza kuri Umucyo")
    assert "Amateka y'ubwishyu" in reply and "Tanga ikibazo cy'ubwishyu" in reply


def test_choosing_english_shows_the_english_menu(api_client, seeded):
    reply = raw(api_client, EN)
    assert reply.startswith("CON Welcome to Umucyo") and "Payment History" in reply


@pytest.mark.parametrize("text", ["0", "3", "9", "x", "12", "*", "1 2"])
def test_an_invalid_language_choice_is_refused_in_both_languages(api_client, seeded, text):
    reply = raw(api_client, text)
    assert reply.startswith("END Invalid choice") and "Amahitamo siyo" in reply


@pytest.mark.parametrize("phone", ["+250799999999", "0788123450"])
def test_an_unregistered_caller_is_told_in_both_languages(api_client, seeded, phone):
    reply = raw(api_client, "", phone=phone)
    assert "You are not registered" in reply and "Ntiwanditswe" in reply


def test_history_menu_in_kinyarwanda(api_client, seeded):
    reply = dial_ussd_language(api_client, "1", RW)
    assert reply == "CON Amateka y'ubwishyu:\n1. Uku kwezi\n2. Amezi 3 ashize"


def test_this_month_in_kinyarwanda(api_client, seeded):
    today = month_start(0)
    reply = dial_ussd_language(api_client, "1*1", RW)
    assert reply.startswith(
        f"END {month_label('rw', today)}\nIbiro: 100.0 kg\nUko bimeze: Wishyuwe ku wa "
    )
    from datetime import date

    assert reply.endswith(format_date("rw", date.today(), True))


def test_three_months_in_kinyarwanda(api_client, seeded):
    lines = dial_ussd_language(api_client, "1*2", RW).split("\n")
    assert lines[0] == "END Amezi 3 ashize:"
    assert lines[1].startswith(
        f"{month_label('rw', month_start(2), short=True)}: 100.0kg, Wishyuwe ku wa "
    )
    assert lines[2] == f"{month_label('rw', month_start(1), short=True)}: 100.0kg, Ntabwo wishyuwe"
    assert lines[3].startswith(
        f"{month_label('rw', month_start(0), short=True)}: 100.0kg, Wishyuwe ku wa "
    )


def test_no_records_in_kinyarwanda(api_client, seeded):
    reply = raw(api_client, f"{RW}*1*1", phone="0788999888")
    assert reply == f"END {month_label('rw', month_start(0))}: Nta makuru ahari."
    assert raw(api_client, f"{RW}*1*2", phone="0788999888").count("nta makuru") == 3


def test_history_shows_the_same_numbers_in_both_languages(api_client, seeded):
    assert "100.0" in dial_ussd_language(api_client, "1*1", RW) and "100.0" in dial_ussd_language(
        api_client, "1*1", EN
    )


def test_report_menu_in_kinyarwanda(api_client, seeded):
    assert (
        dial_ussd_language(api_client, "2", RW)
        == "CON Tanga ikibazo cy'ubwishyu:\n1. Nishyuwe make\n2. Sinishyuwe na gato"
    )


@pytest.mark.parametrize(
    "kind, question", [("1", "Ni ukuhe kwezi wishyuwe make?"), ("2", "Ni ukuhe kwezi utishyuwe?")]
)
def test_month_question_in_kinyarwanda_lists_kinyarwanda_months(api_client, seeded, kind, question):
    reply = dial_ussd_language(api_client, f"2*{kind}", RW)
    assert reply.startswith(f"CON {question}\n")
    for offset in range(3):
        assert f"{offset + 1}. {month_label('rw', month_start(offset))}" in reply


@pytest.mark.parametrize("kind, marker", [("1", "ubwishyu bwa make"), ("2", "kutishyurwa")])
@pytest.mark.parametrize("choice", ["1", "2", "3"])
def test_kinyarwanda_report_sends_a_kinyarwanda_sms(
    api_client, seeded, outbox, kind, marker, choice
):
    assert (
        dial_ussd_language(api_client, f"2*{kind}*{choice}", RW)
        == "END Ikibazo cyawe cyoherejwe neza."
    )
    assert len(outbox) == 1
    phone, text = outbox[0]
    assert phone == FARMER_PHONE
    assert text.startswith("Muraho John, ") and marker in text and text.endswith("kuri koperative.")
    assert month_label("rw", month_start(int(choice) - 1)) in text
    assert len(text) <= 160


@pytest.mark.parametrize("kind", ["1", "2"])
def test_english_report_still_sends_an_english_sms(api_client, seeded, outbox, kind):
    dial_ussd_language(api_client, f"2*{kind}*1", EN)
    assert outbox[0][1].startswith("Dear John, ")


def test_the_cooperative_log_is_always_in_english(api_client, seeded, outbox, caplog):
    caplog.set_level(logging.INFO)
    dial_ussd_language(api_client, "2*1*2", RW)
    assert f"reports LESS PAYMENT for {month_label('en', month_start(1))}" in caplog.text
    assert "Farmer John (0788123456)" in caplog.text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("2*1*9", "END Ukwezi si ko. Ongera uhamagare, ukande 1, 2 cyangwa 3."),
        ("2*5", "END Amahitamo siyo mu gutanga ikibazo."),
        ("1*9", "END Amahitamo siyo mu mateka y'ubwishyu."),
        ("7", "END Amahitamo siyo. Ongera ugerageze."),
    ],
)
def test_errors_in_kinyarwanda(api_client, seeded, outbox, text, expected):
    assert dial_ussd_language(api_client, text, RW) == expected
    assert outbox == []


def test_failure_message_in_kinyarwanda_when_the_sms_cannot_be_sent(
    api_client, seeded, monkeypatch
):
    monkeypatch.setattr(SmsService, "send_custom_sms", lambda self, phone, message: False)
    assert dial_ussd_language(api_client, "2*1*1", RW) == (
        "END Mutwihanganire, ntitwabashije kohereza ikibazo cyawe. Ongera ugerageze nyuma."
    )


ALL_FLOWS = [
    "",
    "1",
    "1*1",
    "1*2",
    "1*9",
    "2",
    "2*1",
    "2*2",
    "2*5",
    "2*1*1",
    "2*1*2",
    "2*1*3",
    "2*2*1",
    "2*2*2",
    "2*2*3",
    "2*1*9",
    "7",
]


@pytest.mark.parametrize("lang", [RW, EN])
@pytest.mark.parametrize("text", ALL_FLOWS)
def test_every_screen_in_both_languages_fits_one_ussd_screen(
    api_client, seeded, outbox, lang, text
):
    reply = dial_ussd_language(api_client, text, lang)
    assert reply.startswith(("CON ", "END ")) and len(reply) <= 182
    assert "{" not in reply and "}" not in reply


@pytest.mark.parametrize("text", ["1*1*1", "1*2*2*1", "2*2*1*2*1", "1*1*1*1", "1**", "1*"])
def test_deep_and_odd_paths_after_choosing_a_language_never_break(api_client, seeded, outbox, text):
    reply = raw(api_client, text)
    assert reply.startswith(("CON ", "END ")) and len(reply) <= 182










def dial_ussd_history_extra(client, text, phone=FARMER_NO_PAYMENTS_PHONE):
    """Default caller is Jane, the farmer who has no payments in the seed data."""
    return client.post(URL, data={"phoneNumber": phone, "text": f"2*{text}"}).text  # 2 = English


def add_payment(
    db,
    seeded,
    offset=0,
    quantity="100",
    status=PaymentStatus.paid,
    paid_on=None,
    period_start=None,
    farmer_id=None,
):
    """A payment for a delivery made on `period_start` (default: first day of the month)."""
    start = period_start or month_start(offset)
    qty = Decimal(str(quantity))
    delivered = datetime(start.year, start.month, start.day, 12, 0, tzinfo=timezone.utc)
    farmer = farmer_id or seeded.farmer2
    record_id = uuid.uuid4()
    db.add(
        ProduceRecord(
            produce_record_id=record_id,
            cooperative_id=seeded.coop,
            produce_price_id=seeded.price,
            farmer_id=farmer,
            device_id=seeded.device,
            collection_point_id=seeded.point,
            delivery_status=DeliveryStatus.accepted,
            user_id=seeded.agent,
            gross_weight_kg=qty,
            agent_notes="x",
            amount=qty * 100,
            recorded_at=delivered,
        )
    )
    db.flush()
    db.add(
        PaymentTransaction(
            farmer_id=farmer,
            user_id=seeded.agent,
            produce_price_id=seeded.price,
            produce_record_id=record_id,
            quantity=qty,
            amount=qty * 100,
            transaction_reference=f"X-{uuid.uuid4().hex}",
            failure_reason="",
            status=status,
            approved_at=paid_on or delivered,
            payment_date=paid_on or delivered,
        )
    )
    db.commit()


def at(day, offset=0):
    first = month_start(offset)
    return datetime(first.year, first.month, day, 9, 0, tzinfo=timezone.utc)


def test_two_paid_payments_in_one_month_are_summed_and_show_the_latest_date(
    api_client, api_db, seeded
):
    add_payment(api_db, seeded, quantity="40", paid_on=at(3))
    add_payment(api_db, seeded, quantity="60.5", paid_on=at(20))
    label = f"{month_start(0):%b %Y}"
    assert (
        dial_ussd_history_extra(api_client, "1*1")
        == f"END {label}\nWeight: 100.5 kg\nStatus: Paid on 20 {label}"
    )


def test_one_pending_payment_makes_the_whole_month_unpaid(api_client, api_db, seeded):
    add_payment(api_db, seeded, quantity="40", paid_on=at(3))
    add_payment(api_db, seeded, quantity="60", status=PaymentStatus.pending)
    assert (
        dial_ussd_history_extra(api_client, "1*1")
        == f"END {month_start(0):%b %Y}\nWeight: 100.0 kg\nStatus: Unpaid"
    )


def test_a_single_pending_payment_is_unpaid(api_client, api_db, seeded):
    add_payment(api_db, seeded, status=PaymentStatus.pending)
    assert dial_ussd_history_extra(api_client, "1*1").endswith("Status: Unpaid")


def test_large_weights_use_thousands_separators(api_client, api_db, seeded):
    add_payment(api_db, seeded, quantity="1500.5", paid_on=at(5))
    assert "Weight: 1,500.5 kg" in dial_ussd_history_extra(api_client, "1*1")


def test_payment_older_than_three_months_is_not_shown(api_client, api_db, seeded):
    add_payment(api_db, seeded, offset=3, paid_on=at(5, 3))
    assert dial_ussd_history_extra(api_client, "1*2").count("no records") == 3


def test_payment_on_the_first_day_belongs_to_this_month(api_client, api_db, seeded):
    add_payment(api_db, seeded, period_start=month_start(0), paid_on=at(5))
    assert "no records" not in dial_ussd_history_extra(api_client, "1*1")


def test_payment_on_the_last_day_of_last_month_belongs_to_last_month(api_client, api_db, seeded):
    add_payment(api_db, seeded, period_start=month_start(0) - timedelta(days=1), paid_on=at(5, 1))
    assert dial_ussd_history_extra(api_client, "1*1").endswith("no records.")
    lines = dial_ussd_history_extra(api_client, "1*2").split("\n")
    assert "kg" in lines[2] and "no records" in lines[3]


def test_history_is_ordered_oldest_to_newest(api_client, api_db, seeded):
    for offset in (0, 1, 2):
        add_payment(api_db, seeded, offset=offset, paid_on=at(5, offset))
    lines = dial_ussd_history_extra(api_client, "1*2").split("\n")
    assert lines[0] == "END Last 3 months:"
    assert lines[1].startswith(f"{month_start(2):%b}:")
    assert lines[2].startswith(f"{month_start(1):%b}:")
    assert lines[3].startswith(f"{month_start(0):%b}:")


def test_each_farmer_only_sees_their_own_payments(api_client, api_db, seeded):
    add_payment(api_db, seeded, quantity="7", paid_on=at(5))  # Jane's
    john = dial_ussd_history_extra(api_client, "1*1", phone=FARMER_PHONE)
    jane = dial_ussd_history_extra(api_client, "1*1")
    assert "Weight: 100.0 kg" in john and "7.0 kg" not in john
    assert "Weight: 7.0 kg" in jane and "100.0 kg" not in jane


def test_history_never_sends_an_sms(api_client, seeded, outbox):
    for text in ("1", "1*1", "1*2", "1*9"):
        dial_ussd_history_extra(api_client, text, phone=FARMER_PHONE)
    assert outbox == []


def test_three_month_history_fits_in_one_ussd_screen(api_client, api_db, seeded):
    for offset in (0, 1, 2):
        add_payment(api_db, seeded, offset=offset, quantity="123456.789", paid_on=at(5, offset))
    assert len(dial_ussd_history_extra(api_client, "1*2")) <= 182


LIMIT = 182


def dial_ussd_robustness(client, text="", phone=FARMER_PHONE, lang="2"):
    """English by default (the first input is the language: 1 = Kinyarwanda, 2 = English)."""
    full = f"{lang}*{text}" if text else lang
    return client.post(URL, data={"phoneNumber": phone, "text": full})


def fix_today(monkeypatch, year, month, day):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(year, month, day)

    monkeypatch.setattr(ussd_module, "date", FixedDate)


GARBAGE = [
    "*",
    "**",
    "***",
    "abc",
    "0",
    "00",
    "99",
    "-1",
    "1*",
    "*1",
    "1**1",
    "2*",
    "2**",
    "2*1*",
    "2*2*",
    "2*1*1*1",
    "2*2*1*1",
    "1*1*1",
    "1*2*3",
    " 1 ",
    "1 * 1",
    "1;DROP TABLE users;--",
    "<script>alert(1)</script>",
    "2*1*٣",
    "1*1*1*1*1*1*1*1*1*1*1*1",
    "9" * 200,
    "éè",
    "1\n1",
    "%",
    "null",
    "None",
]


@pytest.mark.parametrize("text", GARBAGE)
def test_garbage_input_never_breaks_the_reply(api_client, seeded, outbox, text):
    response = dial_ussd_robustness(api_client, text)
    assert response.status_code == 200
    assert response.text.startswith(("CON ", "END "))
    assert len(response.text) <= LIMIT
    assert outbox == []


VALID_FLOWS = [
    "",
    "1",
    "1*1",
    "1*2",
    "2",
    "2*1",
    "2*2",
    "2*1*1",
    "2*1*2",
    "2*1*3",
    "2*2*1",
    "2*2*2",
    "2*2*3",
    "7",
    "1*9",
    "2*9",
    "2*1*9",
]


@pytest.mark.parametrize("text", VALID_FLOWS)
def test_every_reply_fits_in_one_ussd_screen(api_client, seeded, outbox, text):
    assert len(dial_ussd_robustness(api_client, text).text) <= LIMIT


def test_the_same_request_gives_the_same_reply(api_client, seeded):
    for text in ("", "1*2"):
        assert (
            dial_ussd_robustness(api_client, text).text
            == dial_ussd_robustness(api_client, text).text
        )


@pytest.mark.parametrize("kind", ["1", "2"])
@pytest.mark.parametrize("choice", ["1", "2", "3"])
def test_report_sms_names_the_chosen_month_and_fits_one_sms(
    api_client, seeded, outbox, kind, choice
):
    assert (
        dial_ussd_robustness(api_client, f"2*{kind}*{choice}").text
        == "END Your report was sent successfully."
    )
    assert len(outbox) == 1
    phone, text = outbox[0]
    assert phone == FARMER_PHONE
    assert f"{month_start(int(choice) - 1):%b %Y}" in text
    assert len(text) <= 160


def test_report_goes_to_the_farmer_who_dialled(api_client, seeded, outbox, caplog):
    caplog.set_level(logging.INFO)
    dial_ussd_robustness(api_client, "2*2*1", phone=FARMER_NO_PAYMENTS_PHONE)
    assert [phone for phone, _ in outbox] == [FARMER_NO_PAYMENTS_PHONE]
    assert "Dear Jane" in outbox[0][1]
    assert f"Jane ({FARMER_NO_PAYMENTS_PHONE})" in caplog.text


def test_reports_and_history_write_nothing_to_the_database(api_client, api_db, seeded, outbox):
    def counts():
        api_db.expire_all()
        return (
            api_db.query(Task).count(),
            api_db.query(PaymentTransaction).count(),
            api_db.query(ProduceRecord).count(),
            api_db.query(Farmer).count(),
        )

    before = counts()
    for text in ("1*1", "1*2", "2*1*1", "2*2*3"):
        dial_ussd_robustness(api_client, text)
    assert counts() == before
    assert before[0] == 0


def test_phone_number_is_required(api_client, seeded):
    assert api_client.post(URL, data={"text": ""}).status_code == 422


def test_the_old_field_name_is_not_accepted(api_client, seeded):
    assert api_client.post(URL, data={"phone_number": FARMER_PHONE, "text": ""}).status_code == 422


def test_a_json_body_is_not_accepted(api_client, seeded):
    assert api_client.post(URL, json={"phoneNumber": FARMER_PHONE, "text": ""}).status_code == 422


def test_get_is_not_allowed(api_client, seeded):
    assert api_client.get(URL).status_code == 405


def test_extra_form_fields_are_ignored(api_client, seeded):
    response = api_client.post(
        URL, data={"phoneNumber": FARMER_PHONE, "text": "", "networkCode": "63510", "foo": "bar"}
    )
    assert response.status_code == 200 and response.text.startswith("CON ")


@pytest.mark.parametrize("phone", ["+250 788 123 456", "0788-123-456", " 0788123456 "])
def test_phone_numbers_with_spaces_and_dashes_still_match(api_client, seeded, phone):
    assert dial_ussd_robustness(api_client, "", phone=phone).text.startswith("CON ")


@pytest.mark.parametrize("phone", ["0788123450", "+250788123457", "0788", "abcdefghijk"])
def test_numbers_that_are_not_a_registered_farmer_are_refused(api_client, seeded, phone):
    reply = dial_ussd_robustness(api_client, "", phone=phone).text
    assert reply.startswith("END ")
    assert "not registered" in reply or "Invalid phone number" in reply


def test_process_request_survives_a_database_failure():
    db = MagicMock()
    db.query.side_effect = RuntimeError("database is down")
    reply = UssdService(db).process_request("0788123456", "")
    assert reply.startswith("END Sorry, something went wrong. Please try again later.")
    assert "Mutwihanganire" in reply
    db.rollback.assert_called_once()


def test_process_request_survives_any_unexpected_error(api_db, monkeypatch):
    def boom(self, phone, text):
        raise ValueError("unexpected")

    monkeypatch.setattr(UssdService, "_process", boom)
    assert UssdService(api_db).process_request("0788123456", "").startswith("END Sorry")


def test_process_request_accepts_none_text(api_db, seeded):
    assert UssdService(api_db).process_request(FARMER_PHONE, None).startswith("CON ")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0788123456", "788123456"),
        ("+250788123456", "788123456"),
        ("250788123456", "788123456"),
        ("+250 788-123 456", "788123456"),
        ("", ""),
        (None, ""),
        ("abc", ""),
        ("123", "123"),
    ],
)
def test_clean_phone(api_db, raw, expected):
    assert UssdService(api_db)._clean_phone(raw) == expected


def test_months_wrap_over_new_year(api_db, monkeypatch):
    fix_today(monkeypatch, 2026, 1, 15)
    service = UssdService(api_db)
    assert service._month_range(0) == (date(2026, 1, 1), date(2026, 2, 1))
    assert service._month_range(1) == (date(2025, 12, 1), date(2026, 1, 1))
    assert service._month_range(2) == (date(2025, 11, 1), date(2025, 12, 1))


def test_december_ends_on_the_first_of_january(api_db, monkeypatch):
    fix_today(monkeypatch, 2026, 12, 10)
    assert UssdService(api_db)._month_range(0) == (date(2026, 12, 1), date(2027, 1, 1))


def test_month_labels_and_menu_across_new_year(api_db, monkeypatch):
    fix_today(monkeypatch, 2026, 1, 31)
    service = UssdService(api_db)
    assert service._month_label(0) == "Jan 2026"
    assert service._month_label(1) == "Dec 2025"
    assert service._month_label(1, "en", short=True) == "Dec"
    assert service._month_menu("Pick") == "CON Pick\n1. Jan 2026\n2. Dec 2025\n3. Nov 2025"


def test_month_range_on_the_31st_does_not_skip_a_month(api_db, monkeypatch):
    fix_today(monkeypatch, 2026, 3, 31)
    assert UssdService(api_db)._month_range(1) == (date(2026, 2, 1), date(2026, 3, 1))


def use_credentials(monkeypatch, status="Success"):
    fake = make_fake_africastalking(status)
    monkeypatch.setitem(sys.modules, "africastalking", fake)
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "test-key")
    return fake


def test_sends_through_africas_talking(api_db, monkeypatch):
    fake = use_credentials(monkeypatch)
    assert SmsService(api_db).send_custom_sms("0788123456", "Hello") is True
    assert fake.calls["initialize"] == [("sandbox", "test-key")]
    assert fake.calls["send"] == [("Hello", ["+250788123456"])]


def test_phone_numbers_are_converted_to_international_format(api_db, monkeypatch):
    fake = use_credentials(monkeypatch)
    service = SmsService(api_db)
    for phone in ("0788123456", "250788123456", "+250788123456"):
        service.send_custom_sms(phone, "Hi")
    assert [recipients for _, recipients in fake.calls["send"]] == [["+250788123456"]] * 3


def test_a_rejected_sms_returns_false(api_db, monkeypatch):
    fake = use_credentials(monkeypatch, status="InvalidPhoneNumber")
    assert SmsService(api_db).send_custom_sms("0788123456", "Hello") is False
    assert len(fake.calls["send"]) == 1


def test_without_credentials_the_sdk_is_never_used(api_db, monkeypatch):
    monkeypatch.delenv("AT_USERNAME", raising=False)
    monkeypatch.delenv("AT_API_KEY", raising=False)

    class Boom:
        def __getattr__(self, name):
            raise AssertionError("the SDK must not be used without credentials")

    monkeypatch.setitem(sys.modules, "africastalking", Boom())
    assert SmsService(api_db).send_custom_sms("0788123456", "Hello") is False


def test_full_flow_report_confirmation_goes_out_through_africas_talking(
    api_client, seeded, monkeypatch
):
    """USSD report -> real SmsService -> fake Africa's Talking: one confirmation SMS to the farmer."""
    fake = use_credentials(monkeypatch)
    response = api_client.post(
        "/api/v1/ussd/", data={"phoneNumber": "+250788123456", "text": "2*2*2*1"}
    )
    assert response.text == "END Your report was sent successfully."
    assert [recipients for _, recipients in fake.calls["send"]] == [["+250788123456"]]


def test_successful_report_is_saved_with_sms_confirmation(api_client, api_db, seeded, outbox):
    response = api_client.post(
        URL,
        data={
            "phoneNumber": FARMER_PHONE,
            "sessionId": "payment-report-success",
            "serviceCode": "*384*123#",
            "text": "2*2*1*2",
        },
    )

    assert response.status_code == 200
    assert response.text == "END Your report was sent successfully."

    api_db.expire_all()
    reports = api_db.query(PaymentReport).all()

    assert len(reports) == 1

    report = reports[0]
    assert report.farmer_id == seeded.farmer
    assert report.cooperative_id == seeded.coop
    assert report.report_type == "less_payment"
    assert report.reported_month_start == month_start(1)
    assert report.status == "pending"
    assert report.confirmation_sms_sent is True

    assert len(outbox) == 1
    assert outbox[0][0] == FARMER_PHONE


def test_report_is_saved_when_confirmation_sms_fails(api_client, api_db, seeded, monkeypatch):
    monkeypatch.setattr(
        SmsService,
        "send_custom_sms",
        lambda self, phone_number, message: False,
    )

    response = api_client.post(
        URL,
        data={
            "phoneNumber": FARMER_PHONE,
            "sessionId": "payment-report-sms-failure",
            "serviceCode": "*384*123#",
            "text": "2*2*2*1",
        },
    )

    assert response.status_code == 200
    assert response.text.startswith("END Sorry, we could not send your report")

    api_db.expire_all()
    reports = api_db.query(PaymentReport).all()

    assert len(reports) == 1
    assert reports[0].farmer_id == seeded.farmer
    assert reports[0].report_type == "unpaid"
    assert reports[0].reported_month_start == month_start(0)
    assert reports[0].confirmation_sms_sent is False


def test_health_check(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_docs_are_served(api_client):
    response = api_client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_openapi_lists_the_public_routes(api_client):
    paths = api_client.get("/openapi.json").json()["paths"]
    assert "post" in paths["/api/v1/ussd/"]


def test_ussd_documents_the_africas_talking_field_names(api_client):
    schema = api_client.get("/openapi.json").json()
    body = schema["paths"]["/api/v1/ussd/"]["post"]["requestBody"]["content"][
        "application/x-www-form-urlencoded"
    ]
    ref = body["schema"]["$ref"].split("/")[-1]
    fields = schema["components"]["schemas"][ref]["properties"]
    assert {"phoneNumber", "text", "sessionId", "serviceCode"} <= set(fields)


def test_unknown_route_is_a_404(api_client):
    assert api_client.get("/nope").status_code == 404


EN_TEXT, RW_TEXT = STRINGS["en"], STRINGS["rw"]


def placeholders(text):
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


def test_both_languages_have_exactly_the_same_sentences():
    assert set(EN_TEXT) == set(RW_TEXT)


@pytest.mark.parametrize("key", sorted(EN_TEXT))
def test_each_sentence_has_the_same_placeholders_in_both_languages(key):
    assert placeholders(EN_TEXT[key]) == placeholders(RW_TEXT[key])


@pytest.mark.parametrize("key", sorted(EN_TEXT))
def test_no_sentence_is_empty_and_kinyarwanda_is_really_translated(key):
    assert EN_TEXT[key].strip() and RW_TEXT[key].strip()
    if key != "line_record":
        assert RW_TEXT[key] != EN_TEXT[key]


@pytest.mark.parametrize("lang", ["en", "rw"])
@pytest.mark.parametrize("key", sorted(EN_TEXT))
def test_screens_start_with_con_or_end_and_sms_texts_do_not(lang, key):
    text = STRINGS[lang][key]
    is_sms = key.startswith("sms_")
    assert text.startswith(("CON ", "END ")) == (
        not is_sms
        and key
        not in {
            "paid",
            "paid_on",
            "unpaid",
            "line_no_records",
            "line_record",
            "fallback_point",
            "fallback_coop",
            "ask_month_less",
            "ask_month_unpaid",
        }
    )


@pytest.mark.parametrize("text", [LANGUAGE_MENU, *BILINGUAL.values()])
def test_bilingual_screens_fit_one_ussd_screen(text):
    assert text.startswith(("CON ", "END ")) and len(text) <= 182


def test_the_language_menu_offers_both_languages():
    assert "1. Kinyarwanda" in LANGUAGE_MENU and "2. English" in LANGUAGE_MENU
    assert LANGUAGES == {"1": "rw", "2": "en"}


@pytest.mark.parametrize("lang", ["en", "rw"])
def test_twelve_distinct_months(lang):
    for kind in ("long", "short"):
        assert len(MONTHS[lang][kind]) == 12 == len(set(MONTHS[lang][kind]))


def test_kinyarwanda_month_names():
    assert MONTHS["rw"]["long"] == [
        "Mutarama",
        "Gashyantare",
        "Werurwe",
        "Mata",
        "Gicurasi",
        "Kamena",
        "Nyakanga",
        "Kanama",
        "Nzeri",
        "Ukwakira",
        "Ugushyingo",
        "Ukuboza",
    ]


def test_month_labels():
    assert month_label("rw", date(2026, 1, 9)) == "Mutarama 2026"
    assert month_label("rw", date(2026, 10, 9), short=True) == "Ukw"
    assert month_label("en", date(2026, 10, 9)) == "Oct 2026"
    assert month_label("en", date(2026, 10, 9), short=True) == "Oct"


def test_dates():
    assert format_date("rw", date(2026, 10, 5)) == "05 Ukwakira 2026"
    assert format_date("rw", date(2026, 10, 5), with_year=False) == "05 Ukw"
    assert format_date("en", date(2026, 10, 5)) == "05 Oct 2026"
    assert format_date("en", date(2026, 10, 5), with_year=False) == "05 Oct"


def test_an_unknown_language_falls_back_to_english():
    assert DEFAULT_LANGUAGE == "en"
    assert tr("fr", "main_menu") == tr("en", "main_menu")
    assert month_label("fr", date(2026, 10, 1)) == "Oct 2026"
    assert format_date(None, date(2026, 10, 1)) == "01 Oct 2026"


def test_tr_fills_placeholders():
    assert (
        tr("rw", "history_none_month", month="Ukwakira 2026")
        == "END Ukwakira 2026: Nta makuru ahari."
    )
    assert (
        tr(
            "en",
            "sms_delivery",
            name="John",
            weight="25.5",
            point="Main",
            coop="Coop",
            date="05 Oct 2026",
            amount="1,250.00",
        )
        == "Dear John, 25.5 kg of produce was delivered at Main, Coop on 05 Oct 2026. Amount to be paid: RWF 1,250.00."
    )


def test_a_farmer_name_with_braces_does_not_break_the_message():
    assert "{x}" in tr("en", "sms_less", name="{x}", month="Oct 2026")
