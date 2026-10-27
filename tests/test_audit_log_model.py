from models.audit_log import AuditLog


def test_audit_log_table_name():
    assert AuditLog.__tablename__ == "audit_log"


def test_audit_log_has_expected_columns():
    expected = ["audit_log_id", "user_id", "action", "entity_type", "entity_id", "old_values", "new_values", "created_at"]
    assert expected == [column.name for column in AuditLog.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(AuditLog.__table__.columns.keys()))


def test_audit_log_has_primary_key():
    assert AuditLog.__table__.primary_key.columns
