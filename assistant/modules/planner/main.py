"""
Planner Module
==============
Task management with simple weighted priority scoring.
priority = importance*0.6 + urgency*0.3 - effort*0.1
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
TASKS = []


class Task(BaseModel):
    title: str
    urgency: int
    importance: int
    effort: int


def register(app, publish, subscribe):
    app.include_router(router, prefix="/tasks")


@router.post("/add")
def add_task(task: Task):
    TASKS.append(task)
    return {"status": "added", "task": task}


@router.get("/list")
def list_tasks():
    scored = [(t.title, (t.importance * 0.6) + (t.urgency * 0.3) - (t.effort * 0.1)) for t in TASKS]
    sorted_tasks = sorted(scored, key=lambda x: x[1], reverse=True)
    return {"prioritised_tasks": sorted_tasks}
