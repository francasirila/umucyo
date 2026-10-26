import uuid
from models.task import Task
from models.enums import TaskPriority, TaskStatus


def create_mock_task():
    return Task(
        task_id=uuid.uuid4(),
        cooperative_id=uuid.uuid4(),
        farmer_id=uuid.uuid4(),
        created_by_user_id=uuid.uuid4(),
        assigned_to_user_id=uuid.uuid4(),
        collection_point_id=uuid.uuid4(),
        description="Visit",
        priority=TaskPriority.normal,
        status=TaskStatus.open,
    )


def test_task_creation():
    assert create_mock_task().description == "Visit"


def test_task_high_priority():
    task = create_mock_task()
    task.priority = TaskPriority.high
    assert task.priority == TaskPriority.high


def test_task_completed():
    task = create_mock_task()
    task.status = TaskStatus.completed
    assert task.status == TaskStatus.completed


def test_task_unicode_description():
    task = create_mock_task()
    task.description = "Gusura (Tractor)"
    assert "(Tractor)" in task.description


def test_task_missing_description():
    task = create_mock_task()
    task.description = None
    assert task.description is None


def test_task_low_priority():
    task = create_mock_task()
    task.priority = TaskPriority.low
    assert task.priority == TaskPriority.low


def test_task_max_description():
    task = create_mock_task()
    task.description = "A" * 5000
    assert len(task.description) == 5000
