"""
Weekly Review Logic (Phase 3.5 Week 3)
======================================
GTD-style weekly review for planning and reflection.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
import json

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def get_week_stats() -> Dict[str, Any]:
    """
    Get statistics for the past week.

    Returns:
        Dictionary with week statistics
    """
    today = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()
    today_str = today.isoformat()

    stats = {
        "tasks_completed": 0,
        "tasks_created": 0,
        "goals_progressed": 0,
        "habits_completed": 0,
        "habits_total": 0,
        "evening_plans_completed": 0,
        "brain_dump_items_processed": 0,
    }

    with engine.connect() as conn:
        # Tasks completed this week
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM assistant_items
                WHERE status = 'completed'
                AND type = 'task'
                AND updated_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        stats["tasks_completed"] = row[0] if row else 0

        # Tasks created this week
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM assistant_items
                WHERE type = 'task'
                AND created_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        stats["tasks_created"] = row[0] if row else 0

        # Goals with progress
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM assistant_items
                WHERE type = 'goal'
                AND updated_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        stats["goals_progressed"] = row[0] if row else 0

        # Habit completions
        row = conn.execute(
            text(
                """
                SELECT SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), COUNT(*)
                FROM habit_completions
                WHERE completion_date >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        if row:
            stats["habits_completed"] = row[0] or 0
            stats["habits_total"] = row[1] or 0

        # Evening plans
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM daily_reflections
                WHERE date >= :week_ago AND evening_completed = 1
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        stats["evening_plans_completed"] = row[0] if row else 0

        # Brain dump items processed
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM thought_logs
                WHERE processed = 1 AND processed_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()
        stats["brain_dump_items_processed"] = row[0] if row else 0

    return stats


def get_incomplete_items() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all incomplete items for review.

    Returns:
        Dictionary with categorized incomplete items
    """
    result = {
        "overdue_tasks": [],
        "stale_goals": [],
        "unclassified_tasks": [],
        "unprocessed_thoughts": [],
    }

    today = date.today().isoformat()
    two_weeks_ago = (date.today() - timedelta(days=14)).isoformat()

    with engine.connect() as conn:
        # Overdue tasks
        rows = conn.execute(
            text(
                """
                SELECT id, title, date, priority FROM assistant_items
                WHERE type = 'task' AND status IN ('upcoming', 'in_progress')
                AND date < :today
                ORDER BY date ASC
                LIMIT 20
            """
            ),
            {"today": today},
        ).fetchall()

        result["overdue_tasks"] = [
            {"id": r[0], "title": r[1], "date": r[2], "priority": r[3]} for r in rows
        ]

        # Stale goals (no update in 2 weeks)
        rows = conn.execute(
            text(
                """
                SELECT id, title, updated_at FROM assistant_items
                WHERE type = 'goal' AND status IN ('upcoming', 'in_progress')
                AND updated_at < :stale_date
                ORDER BY updated_at ASC
                LIMIT 10
            """
            ),
            {"stale_date": two_weeks_ago},
        ).fetchall()

        result["stale_goals"] = [{"id": r[0], "title": r[1], "last_updated": r[2]} for r in rows]

        # Unclassified tasks (no quadrant)
        rows = conn.execute(
            text(
                """
                SELECT id, title, priority FROM assistant_items
                WHERE type IN ('task', 'goal')
                AND status IN ('upcoming', 'in_progress')
                AND (quadrant IS NULL OR quadrant = '')
                LIMIT 20
            """
            )
        ).fetchall()

        result["unclassified_tasks"] = [{"id": r[0], "title": r[1], "priority": r[2]} for r in rows]

        # Unprocessed thoughts
        rows = conn.execute(
            text(
                """
                SELECT id, content, captured_at FROM thought_logs
                WHERE processed = 0
                ORDER BY captured_at DESC
                LIMIT 20
            """
            )
        ).fetchall()

        result["unprocessed_thoughts"] = [
            {"id": r[0], "content": r[1], "captured_at": r[2]} for r in rows
        ]

    return result


def get_wins_this_week() -> List[Dict[str, Any]]:
    """
    Get completed items from this week (wins to celebrate).
    """
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, title, type, priority FROM assistant_items
                WHERE status = 'completed'
                AND updated_at >= :week_ago
                ORDER BY priority DESC, updated_at DESC
                LIMIT 15
            """
            ),
            {"week_ago": week_ago},
        ).fetchall()

    return [{"id": r[0], "title": r[1], "type": r[2], "priority": r[3]} for r in rows]


def get_streak_summary() -> List[Dict[str, Any]]:
    """
    Get summary of all streaks.
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT activity, current_streak, longest_streak, last_completed, total_completions
                FROM streaks
                ORDER BY current_streak DESC
            """
            )
        ).fetchall()

    return [
        {
            "activity": r[0],
            "current_streak": r[1],
            "longest_streak": r[2],
            "last_completed": r[3],
            "total_completions": r[4],
        }
        for r in rows
    ]


def save_weekly_review(
    wins: List[str],
    lessons: List[str],
    next_week_focus: str,
    obstacles_anticipated: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """
    Save a weekly review.

    Args:
        wins: List of wins from this week
        lessons: List of lessons learned
        next_week_focus: Main focus for next week
        obstacles_anticipated: Potential obstacles
        notes: Additional notes

    Returns:
        The review ID
    """
    today = date.today()
    # Get the Sunday of this week
    week_start = today - timedelta(days=today.weekday() + 1)
    week_end = week_start + timedelta(days=6)

    with engine.begin() as conn:
        # Check if review exists for this week
        existing = conn.execute(
            text(
                """
                SELECT id FROM weekly_reviews WHERE week_start = :week_start
            """
            ),
            {"week_start": week_start.isoformat()},
        ).fetchone()

        if existing:
            # Update existing
            conn.execute(
                text(
                    """
                    UPDATE weekly_reviews
                    SET wins = :wins, lessons = :lessons, next_week_focus = :focus,
                        obstacles_anticipated = :obstacles, notes = :notes,
                        updated_at = :now
                    WHERE id = :id
                """
                ),
                {
                    "id": existing[0],
                    "wins": json.dumps(wins),
                    "lessons": json.dumps(lessons),
                    "focus": next_week_focus,
                    "obstacles": obstacles_anticipated,
                    "notes": notes,
                    "now": datetime.now().isoformat(),
                },
            )
            return existing[0]
        else:
            # Create new
            conn.execute(
                text(
                    """
                    INSERT INTO weekly_reviews
                    (week_start, week_end, wins, lessons, next_week_focus,
                     obstacles_anticipated, notes, created_at)
                    VALUES (:start, :end, :wins, :lessons, :focus, :obstacles, :notes, :now)
                """
                ),
                {
                    "start": week_start.isoformat(),
                    "end": week_end.isoformat(),
                    "wins": json.dumps(wins),
                    "lessons": json.dumps(lessons),
                    "focus": next_week_focus,
                    "obstacles": obstacles_anticipated,
                    "notes": notes,
                    "now": datetime.now().isoformat(),
                },
            )

            row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
            return row[0]


def get_last_weekly_review() -> Optional[Dict[str, Any]]:
    """
    Get the most recent weekly review.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, week_start, week_end, wins, lessons, next_week_focus,
                       obstacles_anticipated, notes, created_at
                FROM weekly_reviews
                ORDER BY week_start DESC
                LIMIT 1
            """
            )
        ).fetchone()

    if not row:
        return None

    wins = []
    lessons = []
    try:
        wins = json.loads(row[3]) if row[3] else []
        lessons = json.loads(row[4]) if row[4] else []
    except:
        pass

    return {
        "id": row[0],
        "week_start": row[1],
        "week_end": row[2],
        "wins": wins,
        "lessons": lessons,
        "next_week_focus": row[5],
        "obstacles_anticipated": row[6],
        "notes": row[7],
        "created_at": row[8],
    }
