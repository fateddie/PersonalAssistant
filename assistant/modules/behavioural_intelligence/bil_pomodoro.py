"""
Pomodoro Timer Logic (Phase 3.5 Week 4)
=======================================
Pomodoro technique implementation for focused work sessions.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

# Standard durations
POMODORO_DURATION = 25  # minutes
SHORT_BREAK = 5  # minutes
LONG_BREAK = 15  # minutes
POMODOROS_BEFORE_LONG_BREAK = 4


def start_pomodoro(
    item_id: Optional[str] = None,
    duration_minutes: int = POMODORO_DURATION,
) -> int:
    """
    Start a new Pomodoro session.

    Args:
        item_id: Optional task/goal ID to associate with
        duration_minutes: Session duration (default 25)

    Returns:
        The session ID
    """
    now = datetime.now()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO pomodoro_sessions (item_id, duration_minutes, started_at, completed)
                VALUES (:item_id, :duration, :started, 0)
            """
            ),
            {
                "item_id": item_id,
                "duration": duration_minutes,
                "started": now.isoformat(),
            },
        )

        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def complete_pomodoro(
    session_id: int,
    accomplishment_notes: Optional[str] = None,
) -> bool:
    """
    Complete a Pomodoro session.

    Args:
        session_id: The session ID
        accomplishment_notes: What was accomplished

    Returns:
        True if successful
    """
    now = datetime.now()

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE pomodoro_sessions
                SET completed = 1, ended_at = :ended, accomplishment_notes = :notes
                WHERE id = :id
            """
            ),
            {
                "id": session_id,
                "ended": now.isoformat(),
                "notes": accomplishment_notes,
            },
        )
        return result.rowcount > 0


def cancel_pomodoro(session_id: int) -> bool:
    """
    Cancel/abandon a Pomodoro session.

    Args:
        session_id: The session ID

    Returns:
        True if successful
    """
    now = datetime.now()

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE pomodoro_sessions
                SET completed = 0, ended_at = :ended
                WHERE id = :id AND ended_at IS NULL
            """
            ),
            {
                "id": session_id,
                "ended": now.isoformat(),
            },
        )
        return result.rowcount > 0


def record_interruption(session_id: int) -> int:
    """
    Record an interruption during a Pomodoro.

    Args:
        session_id: The session ID

    Returns:
        Total interruptions for this session
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE pomodoro_sessions
                SET interruptions = COALESCE(interruptions, 0) + 1
                WHERE id = :id
            """
            ),
            {"id": session_id},
        )

        row = conn.execute(
            text("SELECT interruptions FROM pomodoro_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

        return row[0] if row else 0


def get_active_pomodoro() -> Optional[Dict[str, Any]]:
    """
    Get the currently active Pomodoro session.

    Returns:
        Session dict or None
    """
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, item_id, duration_minutes, started_at, interruptions
                FROM pomodoro_sessions
                WHERE ended_at IS NULL
                ORDER BY started_at DESC
                LIMIT 1
            """
            )
        ).fetchone()

    if not row:
        return None

    started_at = datetime.fromisoformat(row[3])
    elapsed = (datetime.now() - started_at).total_seconds() / 60
    remaining = max(0, row[2] - elapsed)

    return {
        "id": row[0],
        "item_id": row[1],
        "duration_minutes": row[2],
        "started_at": row[3],
        "interruptions": row[4] or 0,
        "elapsed_minutes": round(elapsed, 1),
        "remaining_minutes": round(remaining, 1),
        "is_complete": remaining <= 0,
    }


def get_todays_pomodoros() -> List[Dict[str, Any]]:
    """
    Get all Pomodoro sessions for today.
    """
    today = datetime.now().date().isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT ps.id, ps.item_id, ps.duration_minutes, ps.started_at,
                       ps.ended_at, ps.completed, ps.interruptions,
                       ps.accomplishment_notes, ai.title
                FROM pomodoro_sessions ps
                LEFT JOIN assistant_items ai ON ps.item_id = ai.id
                WHERE date(ps.started_at) = :today
                ORDER BY ps.started_at DESC
            """
            ),
            {"today": today},
        ).fetchall()

    return [
        {
            "id": row[0],
            "item_id": row[1],
            "duration_minutes": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "completed": bool(row[5]),
            "interruptions": row[6] or 0,
            "accomplishment_notes": row[7],
            "task_title": row[8],
        }
        for row in rows
    ]


def get_pomodoro_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get Pomodoro statistics for the specified period.

    Args:
        days: Number of days to look back

    Returns:
        Statistics dictionary
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        # Total completed
        row = conn.execute(
            text(
                """
                SELECT COUNT(*), SUM(duration_minutes), SUM(interruptions)
                FROM pomodoro_sessions
                WHERE completed = 1 AND started_at >= :start
            """
            ),
            {"start": start_date},
        ).fetchone()

        completed = row[0] or 0
        total_minutes = row[1] or 0
        total_interruptions = row[2] or 0

        # Total started (including abandoned)
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pomodoro_sessions
                WHERE started_at >= :start
            """
            ),
            {"start": start_date},
        ).fetchone()

        total_started = row[0] or 0

        # Average interruptions per completed pomodoro
        avg_interruptions = total_interruptions / completed if completed > 0 else 0

        # Best day
        row = conn.execute(
            text(
                """
                SELECT date(started_at), COUNT(*) as cnt
                FROM pomodoro_sessions
                WHERE completed = 1 AND started_at >= :start
                GROUP BY date(started_at)
                ORDER BY cnt DESC
                LIMIT 1
            """
            ),
            {"start": start_date},
        ).fetchone()

        best_day = {"date": row[0], "count": row[1]} if row else None

    return {
        "completed": completed,
        "total_started": total_started,
        "completion_rate": (completed / total_started * 100) if total_started > 0 else 0,
        "total_focus_hours": round(total_minutes / 60, 1),
        "total_interruptions": total_interruptions,
        "avg_interruptions": round(avg_interruptions, 1),
        "best_day": best_day,
    }


def suggest_break_type() -> Dict[str, Any]:
    """
    Suggest the appropriate break type based on completed pomodoros today.

    Returns:
        Break suggestion with duration
    """
    today = datetime.now().date().isoformat()

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pomodoro_sessions
                WHERE completed = 1 AND date(started_at) = :today
            """
            ),
            {"today": today},
        ).fetchone()

    completed_today = row[0] if row else 0

    if completed_today > 0 and completed_today % POMODOROS_BEFORE_LONG_BREAK == 0:
        return {
            "type": "long",
            "duration_minutes": LONG_BREAK,
            "message": f"Great! You've completed {completed_today} pomodoros. Take a longer break!",
        }
    else:
        return {
            "type": "short",
            "duration_minutes": SHORT_BREAK,
            "message": f"Pomodoro #{completed_today + 1} done! Short break time.",
        }
