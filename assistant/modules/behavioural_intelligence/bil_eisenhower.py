"""
BIL Eisenhower Matrix Classification
====================================
Phase 3.5 - Classify tasks into Eisenhower quadrants.

Quadrants:
- I: Urgent & Important (Do First)
- II: Not Urgent & Important (Schedule)
- III: Urgent & Not Important (Delegate)
- IV: Not Urgent & Not Important (Eliminate)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import text

from .bil_config import engine


# Quadrant thresholds (urgency and importance are 1-5 scale)
URGENCY_THRESHOLD = 4  # >= 4 is "urgent"
IMPORTANCE_THRESHOLD = 4  # >= 4 is "important"

# Quadrant metadata
QUADRANT_INFO = {
    "I": {
        "name": "Do First",
        "description": "Urgent & Important - Crisis, deadlines, emergencies",
        "color": "#ef4444",  # Red
        "action": "Do it now",
    },
    "II": {
        "name": "Schedule",
        "description": "Not Urgent & Important - Planning, prevention, development",
        "color": "#10b981",  # Green
        "action": "Schedule time for it",
    },
    "III": {
        "name": "Delegate",
        "description": "Urgent & Not Important - Interruptions, some meetings",
        "color": "#f59e0b",  # Yellow/Amber
        "action": "Delegate if possible",
    },
    "IV": {
        "name": "Eliminate",
        "description": "Not Urgent & Not Important - Time wasters, busy work",
        "color": "#6b7280",  # Gray
        "action": "Consider eliminating",
    },
}


def classify_quadrant(urgency: int, importance: int) -> str:
    """
    Classify task into Eisenhower quadrant based on urgency and importance.

    Args:
        urgency: 1-5 scale (5 = most urgent)
        importance: 1-5 scale (5 = most important)

    Returns:
        Quadrant: "I", "II", "III", or "IV"
    """
    is_urgent = urgency >= URGENCY_THRESHOLD
    is_important = importance >= IMPORTANCE_THRESHOLD

    if is_urgent and is_important:
        return "I"  # Do First
    elif not is_urgent and is_important:
        return "II"  # Schedule
    elif is_urgent and not is_important:
        return "III"  # Delegate
    else:
        return "IV"  # Eliminate


def classify_from_priority(priority: str) -> str:
    """
    Map priority string to quadrant (fallback when urgency/importance not available).

    Args:
        priority: "high", "med", or "low"

    Returns:
        Quadrant: "I", "II", or "IV"
    """
    if priority == "high":
        return "I"  # Assume high priority = urgent & important
    elif priority == "med":
        return "II"  # Medium = important but not urgent
    else:
        return "IV"  # Low = not urgent, not important


def get_quadrant_info(quadrant: str) -> Dict[str, Any]:
    """Get metadata for a quadrant."""
    return QUADRANT_INFO.get(quadrant, QUADRANT_INFO["IV"])


def get_tasks_by_quadrant() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all assistant_items grouped by Eisenhower quadrant.

    Returns:
        {
            "I": [task1, task2, ...],
            "II": [...],
            "III": [...],
            "IV": [...]
        }
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
            "date": row[6],
        }

        # Use stored quadrant or classify from priority
        quadrant = task["quadrant"]
        if not quadrant:
            quadrant = classify_from_priority(task["priority"] or "low")

        if quadrant in result:
            result[quadrant].append(task)

    return result


def update_task_quadrant(item_id: str, quadrant: str) -> bool:
    """
    Update the quadrant for a specific task.

    Args:
        item_id: The assistant_item ID
        quadrant: "I", "II", "III", or "IV"

    Returns:
        True if updated, False otherwise
    """
    if quadrant not in ["I", "II", "III", "IV"]:
        return False

    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE assistant_items SET quadrant = :quadrant WHERE id = :id"),
            {"quadrant": quadrant, "id": item_id},
        )

    return result.rowcount > 0


def auto_classify_unclassified() -> int:
    """
    Auto-classify tasks that don't have a quadrant set.

    Uses priority field as fallback.

    Returns:
        Number of tasks classified
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
        quadrant = classify_from_priority(priority or "low")
        if update_task_quadrant(item_id, quadrant):
            count += 1

    return count


def get_quadrant_summary() -> Dict[str, int]:
    """
    Get count of tasks in each quadrant.

    Returns:
        {"I": 5, "II": 10, "III": 2, "IV": 3}
    """
    tasks_by_quadrant = get_tasks_by_quadrant()
    return {q: len(tasks) for q, tasks in tasks_by_quadrant.items()}
