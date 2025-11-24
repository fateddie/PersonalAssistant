"""
BIL Daily Reflection Storage
============================
CRUD operations for daily_reflections table (Phase 3.5).

Handles evening planning and morning fallback data persistence.
"""

import json
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from pydantic import BaseModel

from .bil_config import engine


class DailyReflection(BaseModel):
    """Pydantic model for daily reflection data"""

    date: date
    planning_date: Optional[date] = None
    what_went_well: Optional[str] = None
    what_got_in_way: Optional[str] = None
    one_thing_learned: Optional[str] = None
    top_priorities: Optional[List[str]] = None
    one_thing_great: Optional[str] = None
    evening_completed: bool = False
    morning_fallback: bool = False
    energy_am: Optional[int] = None
    energy_pm: Optional[int] = None


def save_evening_plan(
    plan_for_date: date,
    top_priorities: List[str],
    one_thing_great: str,
    what_went_well: Optional[str] = None,
    what_got_in_way: Optional[str] = None,
    one_thing_learned: Optional[str] = None,
) -> int:
    """
    Save evening planning session.

    Args:
        plan_for_date: The date this plan is for (usually tomorrow)
        top_priorities: List of top 3 priorities
        one_thing_great: One thing to make the day great
        what_went_well: Reflection on what went well today
        what_got_in_way: Reflection on blockers
        one_thing_learned: Key learning from today

    Returns:
        reflection_id: Database ID of the saved reflection
    """
    priorities_json = json.dumps(top_priorities[:3])  # Max 3 priorities
    planning_date = date.today()

    with engine.begin() as conn:
        # Upsert: Update if exists, insert if not
        result = conn.execute(
            text(
                """
                INSERT INTO daily_reflections (
                    date, planning_date, what_went_well, what_got_in_way,
                    one_thing_learned, top_priorities, one_thing_great,
                    evening_completed, evening_completed_at, morning_fallback
                ) VALUES (
                    :date, :planning_date, :what_went_well, :what_got_in_way,
                    :one_thing_learned, :top_priorities, :one_thing_great,
                    1, :completed_at, 0
                )
                ON CONFLICT(date) DO UPDATE SET
                    planning_date = :planning_date,
                    what_went_well = :what_went_well,
                    what_got_in_way = :what_got_in_way,
                    one_thing_learned = :one_thing_learned,
                    top_priorities = :top_priorities,
                    one_thing_great = :one_thing_great,
                    evening_completed = 1,
                    evening_completed_at = :completed_at,
                    morning_fallback = 0,
                    updated_at = :completed_at
            """
            ),
            {
                "date": plan_for_date.isoformat(),
                "planning_date": planning_date.isoformat(),
                "what_went_well": what_went_well,
                "what_got_in_way": what_got_in_way,
                "one_thing_learned": one_thing_learned,
                "top_priorities": priorities_json,
                "one_thing_great": one_thing_great,
                "completed_at": datetime.now().isoformat(),
            },
        )

    # Get the ID
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM daily_reflections WHERE date = :date"),
            {"date": plan_for_date.isoformat()},
        ).fetchone()

    return row[0] if row else 0


def save_morning_fallback(
    plan_for_date: date,
    top_priorities: List[str],
    one_thing_great: str,
) -> int:
    """
    Save morning fallback plan (when evening was missed).

    Args:
        plan_for_date: Today's date
        top_priorities: Quick top 3 priorities
        one_thing_great: One thing to make today great

    Returns:
        reflection_id: Database ID
    """
    priorities_json = json.dumps(top_priorities[:3])

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO daily_reflections (
                    date, planning_date, top_priorities, one_thing_great,
                    evening_completed, morning_fallback
                ) VALUES (
                    :date, :date, :top_priorities, :one_thing_great,
                    0, 1
                )
                ON CONFLICT(date) DO UPDATE SET
                    top_priorities = :top_priorities,
                    one_thing_great = :one_thing_great,
                    morning_fallback = 1,
                    updated_at = :updated_at
            """
            ),
            {
                "date": plan_for_date.isoformat(),
                "top_priorities": priorities_json,
                "one_thing_great": one_thing_great,
                "updated_at": datetime.now().isoformat(),
            },
        )

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM daily_reflections WHERE date = :date"),
            {"date": plan_for_date.isoformat()},
        ).fetchone()

    return row[0] if row else 0


def get_plan_for_date(target_date: date) -> Optional[Dict[str, Any]]:
    """
    Get the plan for a specific date.

    Args:
        target_date: Date to get plan for

    Returns:
        Plan dict or None if not found
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM daily_reflections WHERE date = :date"),
            {"date": target_date.isoformat()},
        ).fetchone()

    if not row:
        return None

    return _row_to_dict(row)


def get_today_plan() -> Optional[Dict[str, Any]]:
    """Get today's plan."""
    return get_plan_for_date(date.today())


def get_tomorrow_plan() -> Optional[Dict[str, Any]]:
    """Get tomorrow's plan (for evening planning check)."""
    return get_plan_for_date(date.today() + timedelta(days=1))


def check_evening_plan_exists(target_date: date) -> bool:
    """Check if evening plan exists for a date."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT evening_completed FROM daily_reflections
                WHERE date = :date AND evening_completed = 1
            """
            ),
            {"date": target_date.isoformat()},
        ).fetchone()

    return row is not None


def get_recent_reflections(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get reflections for the last N days.

    Args:
        days: Number of days to look back

    Returns:
        List of reflection dicts
    """
    start_date = date.today() - timedelta(days=days)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT * FROM daily_reflections
                WHERE date >= :start_date
                ORDER BY date DESC
            """
            ),
            {"start_date": start_date.isoformat()},
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def update_energy_levels(target_date: date, energy_am: int, energy_pm: int) -> bool:
    """
    Update energy levels for a date.

    Args:
        target_date: Date to update
        energy_am: Morning energy (1-5)
        energy_pm: Afternoon energy (1-5)

    Returns:
        True if updated, False if no record found
    """
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE daily_reflections
                SET energy_am = :energy_am, energy_pm = :energy_pm, updated_at = :updated_at
                WHERE date = :date
            """
            ),
            {
                "date": target_date.isoformat(),
                "energy_am": energy_am,
                "energy_pm": energy_pm,
                "updated_at": datetime.now().isoformat(),
            },
        )

    return result.rowcount > 0


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert database row to dictionary."""
    priorities = []
    if row[6]:  # top_priorities column
        try:
            priorities = json.loads(row[6])
        except json.JSONDecodeError:
            priorities = []

    return {
        "id": row[0],
        "date": row[1],
        "planning_date": row[2],
        "what_went_well": row[3],
        "what_got_in_way": row[4],
        "one_thing_learned": row[5],
        "top_priorities": priorities,
        "one_thing_great": row[7],
        "evening_completed": bool(row[8]),
        "evening_completed_at": row[9],
        "morning_fallback": bool(row[10]),
        "completion_rate": row[11],
        "energy_am": row[12],
        "energy_pm": row[13],
        "created_at": row[14],
        "updated_at": row[15],
    }
