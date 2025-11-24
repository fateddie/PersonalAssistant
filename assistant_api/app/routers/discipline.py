"""
Discipline API Router (Phase 3.5)
=================================
Endpoints for Eisenhower Matrix, time blocking, and discipline features.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/discipline", tags=["discipline"])

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


# ============ Pydantic Models ============


class QuadrantUpdate(BaseModel):
    """Update task quadrant"""

    item_id: str
    quadrant: str = Field(..., pattern="^(I|II|III|IV)$")


class TimeBlockCreate(BaseModel):
    """Create a time block"""

    item_id: str
    start_time: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    sync_to_calendar: bool = True


class TimeBlockResponse(BaseModel):
    """Time block response"""

    id: int
    item_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    calendar_synced: bool
    completed: bool


class DailyPlanCreate(BaseModel):
    """Create daily plan"""

    date: date
    top_priorities: List[str] = Field(..., min_length=1, max_length=3)
    one_thing_great: str
    what_went_well: Optional[str] = None
    what_got_in_way: Optional[str] = None
    is_evening_plan: bool = True


# ============ Eisenhower Matrix Endpoints ============


@router.get("/quadrants")
async def get_tasks_by_quadrant():
    """
    Get all tasks grouped by Eisenhower quadrant.

    Returns:
        Tasks organized by quadrant I, II, III, IV
    """
    result = {"I": [], "II": [], "III": [], "IV": []}

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, title, type, status, priority, quadrant, date
                FROM assistant_items
                WHERE status IN ('upcoming', 'in_progress')
                AND type IN ('task', 'goal', 'deadline')
                ORDER BY date ASC
            """
            )
        ).fetchall()

    for row in rows:
        task = {
            "id": row[0],
            "title": row[1],
            "type": row[2],
            "status": row[3],
            "priority": row[4],
            "quadrant": row[5],
            "date": str(row[6]) if row[6] else None,
        }

        # Use stored quadrant or infer from priority
        quadrant = task["quadrant"]
        if not quadrant:
            priority = task["priority"] or "low"
            if priority == "high":
                quadrant = "I"
            elif priority == "med":
                quadrant = "II"
            else:
                quadrant = "IV"

        if quadrant in result:
            result[quadrant].append(task)

    return {"quadrants": result}


@router.put("/quadrant")
async def update_task_quadrant(data: QuadrantUpdate):
    """
    Update the Eisenhower quadrant for a task.

    Args:
        item_id: The assistant_item ID
        quadrant: "I", "II", "III", or "IV"
    """
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE assistant_items SET quadrant = :quadrant WHERE id = :id"),
            {"quadrant": data.quadrant, "id": data.item_id},
        )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"success": True, "item_id": data.item_id, "quadrant": data.quadrant}


@router.post("/auto-classify")
async def auto_classify_tasks():
    """
    Auto-classify all unclassified tasks based on priority.
    """
    count = 0

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, priority FROM assistant_items
                WHERE quadrant IS NULL
                AND type IN ('task', 'goal', 'deadline')
                AND status IN ('upcoming', 'in_progress')
            """
            )
        ).fetchall()

    for row in rows:
        item_id, priority = row
        priority = priority or "low"

        if priority == "high":
            quadrant = "I"
        elif priority == "med":
            quadrant = "II"
        else:
            quadrant = "IV"

        with engine.begin() as conn:
            conn.execute(
                text("UPDATE assistant_items SET quadrant = :quadrant WHERE id = :id"),
                {"quadrant": quadrant, "id": item_id},
            )
            count += 1

    return {"success": True, "classified_count": count}


# ============ Time Blocking Endpoints ============


@router.post("/time-block", response_model=TimeBlockResponse)
async def create_time_block(data: TimeBlockCreate):
    """
    Create a time block for a task.

    Args:
        item_id: The assistant_item to block time for
        start_time: Start datetime
        duration_minutes: Duration in minutes (15-480)
        sync_to_calendar: Whether to create Google Calendar event
    """
    end_time = data.start_time + datetime.timedelta(minutes=data.duration_minutes)

    with engine.begin() as conn:
        # Check for conflicts
        conflicts = conn.execute(
            text(
                """
                SELECT id FROM time_blocks
                WHERE (start_time < :end_time AND end_time > :start_time)
            """
            ),
            {"start_time": data.start_time.isoformat(), "end_time": end_time.isoformat()},
        ).fetchall()

        if conflicts:
            raise HTTPException(status_code=409, detail="Time block conflicts with existing block")

        # Create time block
        result = conn.execute(
            text(
                """
                INSERT INTO time_blocks (item_id, start_time, end_time, duration_minutes, calendar_synced)
                VALUES (:item_id, :start_time, :end_time, :duration, :synced)
            """
            ),
            {
                "item_id": data.item_id,
                "start_time": data.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": data.duration_minutes,
                "synced": 1 if data.sync_to_calendar else 0,
            },
        )

    # Get the created block
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM time_blocks WHERE item_id = :item_id ORDER BY id DESC LIMIT 1"),
            {"item_id": data.item_id},
        ).fetchone()

    return TimeBlockResponse(
        id=row[0],
        item_id=data.item_id,
        start_time=data.start_time,
        end_time=end_time,
        duration_minutes=data.duration_minutes,
        calendar_synced=data.sync_to_calendar,
        completed=False,
    )


@router.get("/time-blocks")
async def list_time_blocks(date: Optional[str] = None):
    """
    List time blocks, optionally filtered by date.

    Args:
        date: Optional date filter (YYYY-MM-DD)
    """
    query = """
        SELECT tb.id, tb.item_id, tb.start_time, tb.end_time, tb.duration_minutes,
               tb.calendar_synced, tb.completed, ai.title
        FROM time_blocks tb
        LEFT JOIN assistant_items ai ON tb.item_id = ai.id
    """

    params = {}
    if date:
        query += " WHERE date(tb.start_time) = :date"
        params["date"] = date

    query += " ORDER BY tb.start_time ASC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return {
        "time_blocks": [
            {
                "id": row[0],
                "item_id": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "duration_minutes": row[4],
                "calendar_synced": bool(row[5]),
                "completed": bool(row[6]),
                "task_title": row[7],
            }
            for row in rows
        ]
    }


@router.delete("/time-block/{block_id}")
async def delete_time_block(block_id: int):
    """Delete a time block."""
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM time_blocks WHERE id = :id"),
            {"id": block_id},
        )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Time block not found")

    return {"success": True, "deleted_id": block_id}


# ============ Daily Planning Endpoints ============


@router.get("/today-plan")
async def get_today_plan():
    """Get today's daily plan."""
    today = date.today().isoformat()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM daily_reflections WHERE date = :date"),
            {"date": today},
        ).fetchone()

    if not row:
        return {"has_plan": False, "plan": None}

    import json

    priorities = []
    if row[6]:
        try:
            priorities = json.loads(row[6])
        except:
            priorities = []

    return {
        "has_plan": True,
        "plan": {
            "id": row[0],
            "date": row[1],
            "top_priorities": priorities,
            "one_thing_great": row[7],
            "what_went_well": row[3],
            "what_got_in_way": row[4],
            "evening_completed": bool(row[8]),
            "morning_fallback": bool(row[10]),
        },
    }


@router.get("/streaks")
async def get_streaks():
    """Get all discipline streaks."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT activity, current_streak, longest_streak, last_completed, total_completions
                FROM streaks ORDER BY current_streak DESC
            """
            )
        ).fetchall()

    return {
        "streaks": [
            {
                "activity": row[0],
                "current_streak": row[1],
                "longest_streak": row[2],
                "last_completed": row[3],
                "total_completions": row[4],
            }
            for row in rows
        ]
    }
