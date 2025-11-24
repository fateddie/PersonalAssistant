"""
BIL Rituals - Evening Planning & Morning Fallback
=================================================
Phase 3.5 proactive discipline rituals.

Evening planning (6pm) is the primary pattern.
Morning fallback (8am) activates if evening was skipped.
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import text

from .bil_config import engine
from .bil_daily_reflection import (
    check_evening_plan_exists,
    get_today_plan,
    get_tomorrow_plan,
    get_recent_reflections,
)
from .bil_streaks import update_streak


# Prompts for evening planning
EVENING_PLANNING_PROMPTS = [
    "🌙 Time to plan tomorrow! Let's set you up for success.",
    "🌆 Evening planning time! What will make tomorrow great?",
    "✨ Let's reflect on today and prepare for tomorrow.",
]

# Prompts for morning fallback
MORNING_FALLBACK_PROMPTS = [
    "☀️ Good morning! No evening plan found - let's quickly set your priorities.",
    "🌅 Rise and shine! Quick morning planning to start your day right.",
    "⚡ Morning fallback activated - let's get focused for today!",
]


def check_needs_evening_planning() -> Dict[str, Any]:
    """
    Check if user needs to do evening planning.

    Called at 6pm to determine if prompt should be shown.

    Returns:
        {
            "needs_planning": bool,
            "target_date": date,  # Date the plan is for (tomorrow)
            "has_existing_plan": bool,
            "message": str
        }
    """
    tomorrow = date.today() + timedelta(days=1)
    has_plan = check_evening_plan_exists(tomorrow)

    if has_plan:
        return {
            "needs_planning": False,
            "target_date": tomorrow,
            "has_existing_plan": True,
            "message": f"✅ You already have a plan for {tomorrow.strftime('%A, %b %d')}!",
        }

    return {
        "needs_planning": True,
        "target_date": tomorrow,
        "has_existing_plan": False,
        "message": EVENING_PLANNING_PROMPTS[0],
    }


def check_needs_morning_fallback() -> Dict[str, Any]:
    """
    Check if morning fallback is needed.

    Called at 8am to see if evening planning was missed.

    Returns:
        {
            "needs_fallback": bool,
            "target_date": date,  # Today
            "has_evening_plan": bool,
            "message": str
        }
    """
    today = date.today()
    has_evening_plan = check_evening_plan_exists(today)

    if has_evening_plan:
        plan = get_today_plan()
        priorities = plan.get("top_priorities", []) if plan else []
        priority_text = "\n".join([f"  {i+1}. {p}" for i, p in enumerate(priorities)])

        return {
            "needs_fallback": False,
            "target_date": today,
            "has_evening_plan": True,
            "message": f"✅ Your plan for today:\n{priority_text}",
            "plan": plan,
        }

    return {
        "needs_fallback": True,
        "target_date": today,
        "has_evening_plan": False,
        "message": MORNING_FALLBACK_PROMPTS[0],
    }


def get_evening_planning_context() -> Dict[str, Any]:
    """
    Get context for evening planning form.

    Provides data to pre-fill or suggest based on recent activity.

    Returns:
        {
            "target_date": date,
            "today_tasks_completed": int,
            "recent_blockers": list,
            "suggested_priorities": list,
            "streak_info": dict
        }
    """
    tomorrow = date.today() + timedelta(days=1)

    # Get recent reflections to find patterns
    recent = get_recent_reflections(days=7)

    # Extract common blockers
    blockers = []
    for r in recent:
        if r.get("what_got_in_way"):
            blockers.append(r["what_got_in_way"])

    # Get incomplete tasks for suggestions
    suggested = _get_incomplete_tasks(limit=5)

    # Get streak info
    streak = _get_evening_planning_streak()

    return {
        "target_date": tomorrow,
        "today_tasks_completed": _count_today_completed_tasks(),
        "recent_blockers": blockers[:3],
        "suggested_priorities": suggested,
        "streak_info": streak,
    }


def get_morning_display_data() -> Dict[str, Any]:
    """
    Get data for morning plan display.

    Returns:
        {
            "has_plan": bool,
            "plan": dict or None,
            "is_fallback": bool,
            "priorities": list,
            "one_thing_great": str,
            "message": str
        }
    """
    plan = get_today_plan()

    if not plan:
        return {
            "has_plan": False,
            "plan": None,
            "is_fallback": False,
            "priorities": [],
            "one_thing_great": "",
            "message": "No plan for today. Create one now!",
        }

    return {
        "has_plan": True,
        "plan": plan,
        "is_fallback": plan.get("morning_fallback", False),
        "priorities": plan.get("top_priorities", []),
        "one_thing_great": plan.get("one_thing_great", ""),
        "message": "🎯 Your plan for today is ready!",
    }


def on_plan_completed(plan_type: str = "evening") -> None:
    """
    Called when a plan is saved. Updates streaks.

    Args:
        plan_type: "evening" or "morning_fallback"
    """
    if plan_type == "evening":
        update_streak("Evening Planning", completed=True)
    # Morning fallback doesn't count toward streak


def _get_incomplete_tasks(limit: int = 5) -> list:
    """Get incomplete assistant_items for priority suggestions."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT title FROM assistant_items
                WHERE status IN ('upcoming', 'in_progress')
                AND type IN ('task', 'goal')
                ORDER BY
                    CASE priority WHEN 'high' THEN 1 WHEN 'med' THEN 2 ELSE 3 END,
                    date ASC
                LIMIT :limit
            """
            ),
            {"limit": limit},
        ).fetchall()

    return [row[0] for row in rows]


def _count_today_completed_tasks() -> int:
    """Count tasks completed today."""
    today = date.today().isoformat()

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM assistant_items
                WHERE status = 'done'
                AND date(updated_at) = :today
            """
            ),
            {"today": today},
        ).fetchone()

    return row[0] if row else 0


def _get_evening_planning_streak() -> Dict[str, Any]:
    """Get streak info for evening planning."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT current_streak, longest_streak, last_completed
                FROM streaks WHERE activity = 'Evening Planning'
            """
            )
        ).fetchone()

    if not row:
        return {"current": 0, "longest": 0, "last_completed": None}

    return {
        "current": row[0],
        "longest": row[1],
        "last_completed": row[2],
    }
