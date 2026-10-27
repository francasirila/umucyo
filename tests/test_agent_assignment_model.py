from models.agent_assignment import AgentAssignment


def test_agent_assignment_table_name():
    assert AgentAssignment.__tablename__ == "agent_assignment"


def test_agent_assignment_has_expected_columns():
    expected = ["assignment_id", "user_id", "collection_point_id", "assigned_by_user_id", "assigned_at", "ended_at"]
    assert expected == [column.name for column in AgentAssignment.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(AgentAssignment.__table__.columns.keys()))


def test_agent_assignment_has_primary_key():
    assert AgentAssignment.__table__.primary_key.columns
