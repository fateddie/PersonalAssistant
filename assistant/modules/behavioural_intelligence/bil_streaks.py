"""
BIL Streak Tracking
===================
Track streaks for discipline activities (Phase 3.5).
"""

from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text

from .bil_config import engine


def update_streak(activity: str, completed: bool = True) -> Dict[str, Any]:
    """
    Update streak for an activity.

    Args:
        activity: Activity name (e.g., "Evening Planning")
        completed: Whether the activity was completed today

    Returns:
        {
            "activity": str,
            "current_streak": int,
            "longest_streak": int,
            "is_new_record": bool
        }
    """
    today = date.today()

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, current_streak, longest_streak, last_completed
                FROM streaks WHERE activity = :activity
            """
            ),
            {"activity": activity},
        ).fetchone()

    if not row:
        # Create new streak record
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO streaks (activity, current_streak, longest_streak, last_completed, total_completions)
                    VALUES (:activity, :current, :longest, :last_completed, 1)
                """
                ),
                {
                    "activity": activity,
                    "current": 1 if completed else 0,
                    "longest": 1 if completed else 0,
                    "last_completed": today.isoformat() if completed else None,
                },
            )
        return {
            "activity": activity,
            "current_streak": 1 if completed else 0,
            "longest_streak": 1 if completed else 0,
            "is_new_record": completed,
        }

    streak_id, current, longest, last_completed = row

    # Calculate new streak
    if completed:
        if last_completed:
            last_date = date.fromisoformat(str(last_completed)[:10])
            days_since = (today - last_date).days

            if days_since == 0:
                # Already completed today, no change
                new_current = current
            elif days_since == 1:
                # Consecutive day, increment
                new_current = current + 1
            else:
                # Streak broken, start fresh
                new_current = 1
        else:
            new_current = 1

        new_longest = max(longest, new_current)
        is_new_record = new_current > longest

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE streaks SET
                        current_streak = :current,
                        longest_streak = :longest,
                        last_completed = :last_completed,
                        total_completions = total_completions + 1,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                ),
                {
                    "id": streak_id,
                    "current": new_current,
                    "longest": new_longest,
                    "last_completed": today.isoformat(),
                    "updated_at": today.isoformat(),
                },
            )

        return {
            "activity": activity,
            "current_streak": new_current,
            "longest_streak": new_longest,
            "is_new_record": is_new_record,
        }
    else:
        # Not completed - check if streak should be reset
        if last_completed:
            last_date = date.fromisoformat(str(last_completed)[:10])
            days_since = (today - last_date).days

            if days_since > 1:
                # Streak broken
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            UPDATE streaks SET current_streak = 0, updated_at = :updated_at
                            WHERE id = :id
                        """
                        ),
                        {"id": streak_id, "updated_at": today.isoformat()},
                    )
                return {
                    "activity": activity,
                    "current_streak": 0,
                    "longest_streak": longest,
                    "is_new_record": False,
                }

        return {
            "activity": activity,
            "current_streak": current,
            "longest_streak": longest,
            "is_new_record": False,
        }


def get_all_streaks() -> List[Dict[str, Any]]:
    """Get all streak records."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT activity, current_streak, longest_streak, last_completed, total_completions
                FROM streaks ORDER BY current_streak DESC
            """
            )
        ).fetchall()

    return [
        {
            "activity": row[0],
            "current_streak": row[1],
            "longest_streak": row[2],
            "last_completed": row[3],
            "total_completions": row[4],
        }
        for row in rows
    ]


def get_streak(activity: str) -> Optional[Dict[str, Any]]:
    """Get streak for a specific activity."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT activity, current_streak, longest_streak, last_completed, total_completions
                FROM streaks WHERE activity = :activity
            """
            ),
            {"activity": activity},
        ).fetchone()

    if not row:
        return None

    return {
        "activity": row[0],
        "current_streak": row[1],
        "longest_streak": row[2],
        "last_completed": row[3],
        "total_completions": row[4],
    }


def get_at_risk_streaks() -> List[Dict[str, Any]]:
    """
    Get streaks that are at risk of being broken.

    Returns streaks where last_completed was yesterday.
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT activity, current_streak, longest_streak, last_completed
                FROM streaks
                WHERE date(last_completed) = :yesterday
                AND current_streak > 0
            """
            ),
            {"yesterday": yesterday},
        ).fetchall()

    return [
        {
            "activity": row[0],
            "current_streak": row[1],
            "longest_streak": row[2],
            "last_completed": row[3],
            "at_risk": True,
        }
        for row in rows
    ]
