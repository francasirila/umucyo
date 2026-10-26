import uuid
from models.agent_assignemt import AgentAssignment

def create_mock_assignment():
    return AgentAssignment(assignment_id=uuid.uuid4(), user_id=uuid.uuid4(), cooperative_id=uuid.uuid4(), collection_point_id=uuid.uuid4(), assigned_by_user_id=uuid.uuid4())

def test_agent_assignment_creation():
    assert create_mock_assignment().assignment_id is not None

def test_agent_assignment_ended_at_null():
    assign = create_mock_assignment()
    assign.ended_at = None
    assert assign.ended_at is None

def test_agent_assignment_status_missing():
    assign = create_mock_assignment()
    assert not hasattr(assign, "status")

def test_agent_assignment_ended_at_set():
    assign = create_mock_assignment()
    assign.ended_at = "2026-01-01"
    assert assign.ended_at == "2026-01-01"