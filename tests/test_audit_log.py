import uuid
from models.audit_log import AuditLog

def test_audit_creation():
    log = AuditLog(audit_log_id=uuid.uuid4(), user_id=uuid.uuid4(), action="create", entity_type="User", entity_id=uuid.uuid4())
    assert log.action == "create"

def test_audit_old_values():
    log = AuditLog(audit_log_id=uuid.uuid4(), user_id=uuid.uuid4(), action="update", entity_type="User", entity_id=uuid.uuid4(), old_values={"name": "A"})
    assert log.old_values["name"] == "A"

def test_audit_new_values():
    log = AuditLog(audit_log_id=uuid.uuid4(), user_id=uuid.uuid4(), action="update", entity_type="User", entity_id=uuid.uuid4(), new_values={"name": "B"})
    assert log.new_values["name"] == "B"

def test_audit_missing_entity_id():
    log = AuditLog(audit_log_id=uuid.uuid4(), user_id=uuid.uuid4(), action="delete", entity_type="User", entity_id=None)
    assert log.entity_id is None

def test_audit_action_delete():
    log = AuditLog(audit_log_id=uuid.uuid4(), user_id=uuid.uuid4(), action="delete", entity_type="User", entity_id=uuid.uuid4())
    assert log.action == "delete"