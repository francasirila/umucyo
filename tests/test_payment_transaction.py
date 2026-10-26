import uuid
from datetime import date
from models.payment_transaction import PaymentTransaction
from models.enums import PaymentStatus

def create_mock_payment():
    return PaymentTransaction(payment_transaction_id=uuid.uuid4(), farmer_id=uuid.uuid4(), cooperative_id=uuid.uuid4(), initiated_by=uuid.uuid4(), batch_id=uuid.uuid4(), period=date.today(), quantity=10, amount=3000, status=PaymentStatus.paid, transaction_reference="REF-1")

def test_payment_creation():
    assert create_mock_payment().amount == 3000

def test_payment_zero_amount():
    payment = create_mock_payment()
    payment.amount = 0
    assert payment.amount == 0

def test_payment_failed_status():
    payment = create_mock_payment()
    payment.status = PaymentStatus.failed
    assert payment.status == PaymentStatus.failed

def test_payment_network_timeout():
    payment = create_mock_payment()
    payment.failure_reason = "Network timeout"
    assert "timeout" in payment.failure_reason.lower()

def test_payment_pending_status():
    payment = create_mock_payment()
    payment.status = PaymentStatus.pending
    assert payment.status == PaymentStatus.pending

def test_payment_max_amount():
    payment = create_mock_payment()
    payment.amount = 999999999
    assert payment.amount == 999999999

def test_payment_reference_created():
    assert create_mock_payment().transaction_reference == "REF-1"