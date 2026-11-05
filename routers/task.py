from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from database import get_db
from schemas.task import TaskCreate, TaskResponse, TaskUpdate
from services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    return TaskService(db).create(payload)


@router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    skip: int = Query(default=0),
    limit: int = Query(default=100),
    db: Session = Depends(get_db),
):
    return TaskService(db).list_tasks(skip=skip, limit=limit)


@router.get("/agent/{agent_id}", response_model=list[TaskResponse])
def list_agent_tasks(
    agent_id: UUID,
    skip: int = Query(default=0),
    limit: int = Query(default=100),
    db: Session = Depends(get_db),
):
    return TaskService(db).list_tasks_by_agent(
        agent_id=agent_id,
        skip=skip,
        limit=limit,
    )
    

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
):
    return TaskService(db).get_task(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    return TaskService(db).update(task_id, payload)


@router.delete(
    "/{task_id}",
    status_code=204,
)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
):
    TaskService(db).delete(task_id)
    return Response(status_code=204)
