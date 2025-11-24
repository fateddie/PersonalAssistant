"""
Habit Stacking Logic (Phase 3.5 Week 3)
=======================================
Implementation of habit chaining using "After X, I will Y" pattern.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
import json

# Database connection
DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def create_habit_chain(
    trigger_habit: str,
    new_habit: str,
    time_of_day: str = "morning",
    description: Optional[str] = None,
) -> int:
    """
    Create a habit chain (habit stacking).

    Args:
        trigger_habit: The existing habit that triggers the new one
        new_habit: The new habit to build
        time_of_day: morning, afternoon, evening
        description: Optional description

    Returns:
        The chain_id
    """
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO habit_chains (trigger_habit, new_habit, time_of_day, description, active)
                VALUES (:trigger, :new, :time, :desc, 1)
            """
            ),
            {
                "trigger": trigger_habit,
                "new": new_habit,
                "time": time_of_day,
                "desc": description,
            },
        )

        # Get the inserted ID
        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def get_habit_chains(active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Get all habit chains.

    Args:
        active_only: If True, only return active chains

    Returns:
        List of habit chain dictionaries
    """
    query = """
        SELECT id, trigger_habit, new_habit, time_of_day, description, active,
               created_at, success_count, total_attempts
        FROM habit_chains
    """

    if active_only:
        query += " WHERE active = 1"

    query += " ORDER BY time_of_day, created_at"

    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    return [
        {
            "id": row[0],
            "trigger_habit": row[1],
            "new_habit": row[2],
            "time_of_day": row[3],
            "description": row[4],
            "active": bool(row[5]),
            "created_at": row[6],
            "success_count": row[7] or 0,
            "total_attempts": row[8] or 0,
            "success_rate": (row[7] / row[8] * 100) if row[8] and row[8] > 0 else 0,
        }
        for row in rows
    ]


def get_chains_by_time(time_of_day: str) -> List[Dict[str, Any]]:
    """Get habit chains for a specific time of day."""
    chains = get_habit_chains(active_only=True)
    return [c for c in chains if c["time_of_day"] == time_of_day]


def record_habit_completion(
    chain_id: int,
    completed: bool,
    notes: Optional[str] = None,
) -> None:
    """
    Record completion of a habit chain.

    Args:
        chain_id: The habit chain ID
        completed: Whether the habit was completed
        notes: Optional notes
    """
    today = date.today().isoformat()

    with engine.begin() as conn:
        # Record in habit_completions
        conn.execute(
            text(
                """
                INSERT INTO habit_completions (chain_id, completion_date, completed, notes)
                VALUES (:chain_id, :date, :completed, :notes)
            """
            ),
            {
                "chain_id": chain_id,
                "date": today,
                "completed": 1 if completed else 0,
                "notes": notes,
            },
        )

        # Update chain stats
        if completed:
            conn.execute(
                text(
                    """
                    UPDATE habit_chains
                    SET success_count = COALESCE(success_count, 0) + 1,
                        total_attempts = COALESCE(total_attempts, 0) + 1
                    WHERE id = :id
                """
                ),
                {"id": chain_id},
            )
        else:
            conn.execute(
                text(
                    """
                    UPDATE habit_chains
                    SET total_attempts = COALESCE(total_attempts, 0) + 1
                    WHERE id = :id
                """
                ),
                {"id": chain_id},
            )


def get_habit_history(chain_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get completion history for a habit chain.

    Args:
        chain_id: The habit chain ID
        days: Number of days to look back

    Returns:
        List of completion records
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT completion_date, completed, notes
                FROM habit_completions
                WHERE chain_id = :chain_id AND completion_date >= :start
                ORDER BY completion_date DESC
            """
            ),
            {"chain_id": chain_id, "start": start_date},
        ).fetchall()

    return [
        {
            "date": row[0],
            "completed": bool(row[1]),
            "notes": row[2],
        }
        for row in rows
    ]


def delete_habit_chain(chain_id: int) -> bool:
    """
    Deactivate a habit chain (soft delete).

    Args:
        chain_id: The chain to deactivate

    Returns:
        True if successful
    """
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE habit_chains SET active = 0 WHERE id = :id"),
            {"id": chain_id},
        )
        return result.rowcount > 0


def get_todays_habits() -> List[Dict[str, Any]]:
    """
    Get all habit chains due for today, with completion status.
    """
    today = date.today().isoformat()
    chains = get_habit_chains(active_only=True)

    # Check today's completions
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT chain_id, completed FROM habit_completions
                WHERE completion_date = :date
            """
            ),
            {"date": today},
        ).fetchall()

    completed_today = {row[0]: bool(row[1]) for row in rows}

    for chain in chains:
        chain["completed_today"] = completed_today.get(chain["id"], None)

    return chains


# ============ If-Then Planning ============


def create_if_then_plan(
    if_situation: str,
    then_action: str,
    category: str = "general",
    related_goal_id: Optional[str] = None,
) -> int:
    """
    Create an If-Then plan (implementation intention).

    Args:
        if_situation: The triggering situation
        then_action: The planned response
        category: Category (procrastination, distraction, emotion, etc.)
        related_goal_id: Optional link to a goal

    Returns:
        The plan ID
    """
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO if_then_plans (if_situation, then_action, category, related_goal_id, active, times_used)
                VALUES (:if_sit, :then_act, :category, :goal_id, 1, 0)
            """
            ),
            {
                "if_sit": if_situation,
                "then_act": then_action,
                "category": category,
                "goal_id": related_goal_id,
            },
        )

        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def get_if_then_plans(
    category: Optional[str] = None,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get If-Then plans.

    Args:
        category: Optional filter by category
        active_only: If True, only return active plans

    Returns:
        List of If-Then plan dictionaries
    """
    query = """
        SELECT id, if_situation, then_action, category, related_goal_id,
               active, times_used, times_successful, created_at
        FROM if_then_plans
        WHERE 1=1
    """
    params = {}

    if active_only:
        query += " AND active = 1"

    if category:
        query += " AND category = :category"
        params["category"] = category

    query += " ORDER BY times_used DESC, created_at DESC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "id": row[0],
            "if_situation": row[1],
            "then_action": row[2],
            "category": row[3],
            "related_goal_id": row[4],
            "active": bool(row[5]),
            "times_used": row[6] or 0,
            "times_successful": row[7] or 0,
            "success_rate": (row[7] / row[6] * 100) if row[6] and row[6] > 0 else 0,
            "created_at": row[8],
        }
        for row in rows
    ]


def record_if_then_usage(plan_id: int, successful: bool) -> None:
    """
    Record usage of an If-Then plan.

    Args:
        plan_id: The plan ID
        successful: Whether it was successful
    """
    with engine.begin() as conn:
        if successful:
            conn.execute(
                text(
                    """
                    UPDATE if_then_plans
                    SET times_used = COALESCE(times_used, 0) + 1,
                        times_successful = COALESCE(times_successful, 0) + 1
                    WHERE id = :id
                """
                ),
                {"id": plan_id},
            )
        else:
            conn.execute(
                text(
                    """
                    UPDATE if_then_plans
                    SET times_used = COALESCE(times_used, 0) + 1
                    WHERE id = :id
                """
                ),
                {"id": plan_id},
            )


def get_suggested_if_then_plans() -> List[Dict[str, str]]:
    """
    Get suggested If-Then plan templates.
    """
    return [
        {
            "category": "procrastination",
            "if_situation": "I feel like putting off a task",
            "then_action": "I will work on it for just 2 minutes",
        },
        {
            "category": "procrastination",
            "if_situation": "I open social media during work",
            "then_action": "I will close it and take 3 deep breaths",
        },
        {
            "category": "distraction",
            "if_situation": "I get a non-urgent notification",
            "then_action": "I will note it and check after my current task",
        },
        {
            "category": "distraction",
            "if_situation": "Someone interrupts my focus time",
            "then_action": "I will say 'Let me finish this thought and I'll be with you'",
        },
        {
            "category": "emotion",
            "if_situation": "I feel overwhelmed by my task list",
            "then_action": "I will pick the one smallest task and do it immediately",
        },
        {
            "category": "emotion",
            "if_situation": "I feel anxious about a deadline",
            "then_action": "I will break it into 3 smaller steps and start the first one",
        },
        {
            "category": "energy",
            "if_situation": "I feel my energy dropping",
            "then_action": "I will take a 5-minute walk or do 10 stretches",
        },
        {
            "category": "energy",
            "if_situation": "It's 3pm and I'm tired",
            "then_action": "I will drink water and do a quick breathing exercise",
        },
    ]


# ============ GTD Brain Dump ============


def save_brain_dump(items: List[str]) -> int:
    """
    Save a brain dump session (quick capture of thoughts/tasks).

    Args:
        items: List of captured items

    Returns:
        Number of items saved
    """
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    count = 0
    with engine.begin() as conn:
        for item in items:
            item = item.strip()
            if not item:
                continue

            conn.execute(
                text(
                    """
                    INSERT INTO thought_logs (content, captured_at, processed, source)
                    VALUES (:content, :captured, 0, 'brain_dump')
                """
                ),
                {
                    "content": item,
                    "captured": now,
                },
            )
            count += 1

    return count


def get_unprocessed_thoughts() -> List[Dict[str, Any]]:
    """
    Get all unprocessed thoughts from brain dumps.
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, content, captured_at, source
                FROM thought_logs
                WHERE processed = 0
                ORDER BY captured_at DESC
            """
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "content": row[1],
            "captured_at": row[2],
            "source": row[3],
        }
        for row in rows
    ]


def mark_thought_processed(thought_id: int, action_taken: Optional[str] = None) -> None:
    """
    Mark a thought as processed.

    Args:
        thought_id: The thought ID
        action_taken: What was done with it (e.g., "converted_to_task", "deleted", "delegated")
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE thought_logs
                SET processed = 1, processed_at = :now, action_taken = :action
                WHERE id = :id
            """
            ),
            {
                "id": thought_id,
                "now": datetime.now().isoformat(),
                "action": action_taken,
            },
        )


def convert_thought_to_task(thought_id: int, title: str, priority: str = "med") -> str:
    """
    Convert a thought to a task in assistant_items.

    Args:
        thought_id: The thought ID
        title: Task title (can be modified from original thought)
        priority: Task priority

    Returns:
        The new task ID
    """
    import uuid

    task_id = str(uuid.uuid4())
    today = date.today().isoformat()

    with engine.begin() as conn:
        # Create task
        conn.execute(
            text(
                """
                INSERT INTO assistant_items (id, type, title, status, priority, date, created_at)
                VALUES (:id, 'task', :title, 'upcoming', :priority, :date, :now)
            """
            ),
            {
                "id": task_id,
                "title": title,
                "priority": priority,
                "date": today,
                "now": datetime.now().isoformat(),
            },
        )

        # Mark thought as processed
        conn.execute(
            text(
                """
                UPDATE thought_logs
                SET processed = 1, processed_at = :now, action_taken = 'converted_to_task'
                WHERE id = :id
            """
            ),
            {
                "id": thought_id,
                "now": datetime.now().isoformat(),
            },
        )

    return task_id
