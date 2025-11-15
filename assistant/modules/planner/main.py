"""
Planner Module
==============
Task management with simple weighted priority scoring.
priority = importance*0.6 + urgency*0.3 - effort*0.1

Database: Uses SQLite (assistant/data/memory.db)
Table: tasks (id, title, urgency, importance, effort, completed, created_at, deadline, project, category, notes, tags, context)
"""

import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from pathlib import Path

router = APIRouter()

# Database connection
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///assistant/data/memory.db")
engine = create_engine(DB_PATH.replace("sqlite:///", "sqlite:///"))


class Task(BaseModel):
    title: str
    urgency: int
    importance: int
    effort: int
    deadline: str | None = None
    project: str | None = None
    category: str | None = None
    notes: str | None = None
    tags: str | None = None
    context: str | None = None


class TaskUpdate(BaseModel):
    """Partial update model - all fields optional"""
    title: str | None = None
    urgency: int | None = None
    importance: int | None = None
    effort: int | None = None
    deadline: str | None = None
    project: str | None = None
    category: str | None = None
    notes: str | None = None
    tags: str | None = None
    context: str | None = None


def register(app, publish, subscribe):
    app.include_router(router, prefix="/tasks")
    print("✅ Planner module loaded (database-backed)")


@router.post("/add")
def add_task(task: Task):
    """
    Add a new task to the database.

    Args:
        task: Task with title, urgency, importance, effort (required)
              + optional: deadline, project, category, notes, tags, context

    Returns:
        {"status": "added", "task_id": int, "task": dict}
    """
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO tasks (title, urgency, importance, effort, completed,
                                     deadline, project, category, notes, tags, context)
                    VALUES (:title, :urgency, :importance, :effort, 0,
                           :deadline, :project, :category, :notes, :tags, :context)
                """),
                {
                    "title": task.title,
                    "urgency": task.urgency,
                    "importance": task.importance,
                    "effort": task.effort,
                    "deadline": task.deadline,
                    "project": task.project,
                    "category": task.category,
                    "notes": task.notes,
                    "tags": task.tags,
                    "context": task.context
                }
            )
            task_id = result.lastrowid

        print(f"✅ Task added to database: {task.title} (ID: {task_id})")

        return {
            "status": "added",
            "task_id": task_id,
            "task": {
                "id": task_id,
                "title": task.title,
                "urgency": task.urgency,
                "importance": task.importance,
                "effort": task.effort,
                "completed": 0,
                "deadline": task.deadline,
                "project": task.project,
                "category": task.category,
                "notes": task.notes,
                "tags": task.tags,
                "context": task.context
            }
        }

    except Exception as e:
        print(f"❌ Error adding task: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding task: {str(e)}")


@router.get("/list")
def list_tasks():
    """
    List all incomplete tasks, sorted by priority score.

    Priority formula: importance*0.6 + urgency*0.3 - effort*0.1

    Returns:
        {"prioritised_tasks": [(title, priority_score), ...]}
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, title, urgency, importance, effort
                    FROM tasks
                    WHERE completed = 0
                    ORDER BY created_at DESC
                """)
            )
            tasks = result.fetchall()

        if not tasks:
            return {"prioritised_tasks": []}

        # Calculate priority scores
        scored = [
            (
                row[1],  # title
                (row[3] * 0.6) + (row[2] * 0.3) - (row[4] * 0.1)  # priority score
            )
            for row in tasks
        ]

        # Sort by priority (highest first)
        sorted_tasks = sorted(scored, key=lambda x: x[1], reverse=True)

        return {"prioritised_tasks": sorted_tasks}

    except Exception as e:
        print(f"❌ Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")


@router.put("/update/{task_id}")
def update_task(task_id: int, updates: TaskUpdate):
    """
    Update an existing task with partial updates.

    Args:
        task_id: ID of the task to update
        updates: TaskUpdate with fields to update (all optional)

    Returns:
        {"status": "updated", "task_id": int, "task": dict}
    """
    try:
        # Build dynamic UPDATE query based on provided fields
        update_fields = []
        update_values = {"task_id": task_id}

        for field, value in updates.dict(exclude_unset=True).items():
            update_fields.append(f"{field} = :{field}")
            update_values[field] = value

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute UPDATE
        with engine.begin() as conn:
            conn.execute(
                text(f"""
                    UPDATE tasks
                    SET {', '.join(update_fields)}
                    WHERE id = :task_id
                """),
                update_values
            )

            # Fetch updated task
            result = conn.execute(
                text("""
                    SELECT id, title, urgency, importance, effort, completed,
                           deadline, project, category, notes, tags, context
                    FROM tasks
                    WHERE id = :task_id
                """),
                {"task_id": task_id}
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        print(f"✅ Task updated: {row[1]} (ID: {task_id})")

        return {
            "status": "updated",
            "task_id": task_id,
            "task": {
                "id": row[0],
                "title": row[1],
                "urgency": row[2],
                "importance": row[3],
                "effort": row[4],
                "completed": row[5],
                "deadline": row[6],
                "project": row[7],
                "category": row[8],
                "notes": row[9],
                "tags": row[10],
                "context": row[11]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@router.delete("/delete/{task_id}")
def delete_task(task_id: int):
    """
    Delete a task (soft delete - marks as completed and deleted).

    Args:
        task_id: ID of the task to delete

    Returns:
        {"status": "deleted", "task_id": int}
    """
    try:
        # Check if task exists
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title FROM tasks WHERE id = :task_id"),
                {"task_id": task_id}
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task_title = row[0]

        # Soft delete: mark as completed and add deleted flag
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE tasks
                    SET completed = 1
                    WHERE id = :task_id
                """),
                {"task_id": task_id}
            )

        print(f"✅ Task deleted: {task_title} (ID: {task_id})")

        return {
            "status": "deleted",
            "task_id": task_id,
            "title": task_title
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")
