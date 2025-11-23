"""
BIL Goals CRUD
==============
Goals create, read, update, delete endpoints.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from sqlalchemy import text

from .bil_config import engine
from .bil_models import Goal, GoalWithCalendar

router = APIRouter()


@router.post("/goals")
def create_goal(goal: Goal):
    """Create a new behavioral goal"""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
            INSERT INTO goals (name, target_per_week, last_update)
            VALUES (:name, :target, :now)
        """
            ),
            {"name": goal.name, "target": goal.target_per_week, "now": datetime.now()},
        )
        goal_id = result.lastrowid

    return {
        "status": "created",
        "goal_id": goal_id,
        "message": f"✅ Goal '{goal.name}' created - targeting {goal.target_per_week}x/week",
    }


@router.post("/goals/with-calendar")
def create_goal_with_calendar(goal: GoalWithCalendar):
    """
    Create a new goal with optional calendar integration.

    If calendar fields are provided (recurring_days, session_time_start, session_time_end),
    creates calendar config in goal_calendar_config table.

    Returns goal_id and calendar_config if calendar was configured.
    """
    from assistant.modules.calendar.helpers import validate_calendar_config

    # Create the goal first
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
            INSERT INTO goals (name, target_per_week, last_update)
            VALUES (:name, :target, :now)
        """
            ),
            {"name": goal.name, "target": goal.target_per_week, "now": datetime.now()},
        )
        goal_id = result.lastrowid

        # If calendar fields provided, validate and save config
        calendar_config = None
        if goal.recurring_days and goal.session_time_start and goal.session_time_end:
            # Validate calendar configuration
            validation = validate_calendar_config(
                goal.recurring_days, goal.session_time_start, goal.session_time_end
            )

            if not validation.get("valid"):
                # Rollback goal creation
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid calendar configuration: {validation.get('error')}",
                )

            # Save calendar config
            conn.execute(
                text(
                    """
                INSERT INTO goal_calendar_config
                (goal_id, recurring_days, session_time_start, session_time_end, weeks_ahead, timezone, is_active)
                VALUES (:goal_id, :recurring_days, :session_time_start, :session_time_end, :weeks_ahead, :timezone, 1)
            """
                ),
                {
                    "goal_id": goal_id,
                    "recurring_days": ",".join(validation["parsed_days"]),
                    "session_time_start": validation["formatted_start"],
                    "session_time_end": validation["formatted_end"],
                    "weeks_ahead": goal.weeks_ahead or 4,
                    "timezone": goal.timezone,
                },
            )

            calendar_config = {
                "recurring_days": validation["parsed_days"],
                "session_time_start": validation["formatted_start"],
                "session_time_end": validation["formatted_end"],
                "weeks_ahead": goal.weeks_ahead or 4,
                "ready_for_calendar_creation": True,
            }

    message = f"✅ Goal '{goal.name}' created - targeting {goal.target_per_week}x/week"
    if calendar_config:
        message += f" with calendar on {', '.join(calendar_config['recurring_days'])}"

    return {
        "status": "created",
        "goal_id": goal_id,
        "calendar_config": calendar_config,
        "message": message,
    }


@router.get("/goals")
def list_goals(status: str = "active"):
    """
    List goals filtered by status.

    Query params:
        status: Filter by status (values: 'active', 'pending', 'archived', 'rejected', 'all')
                Default: 'active' (only show active goals)

    Returns:
        {
            "goals": [...],
            "pending_goals": [...],  # Only if status='pending' or 'all'
            "active_count": int,
            "pending_count": int
        }
    """
    # Build WHERE clause based on status filter
    where_clause = ""
    if status != "all":
        where_clause = f"WHERE status = '{status}'"

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM goals {where_clause} ORDER BY id"))

        active_goals = []
        pending_goals = []

        for row in result:
            goal_dict = {
                "id": row[0],
                "name": row[1],
                "target_per_week": row[2],
                "completed": row[3],
                "last_update": row[4],
                "status": row[5] if len(row) > 5 else "active",
            }

            # Separate by status for detailed response
            if goal_dict["status"] == "active":
                active_goals.append(goal_dict)
            elif goal_dict["status"] == "pending":
                pending_goals.append(goal_dict)

        all_goals = active_goals + pending_goals

    return {
        "goals": (
            all_goals
            if status == "all"
            else (active_goals if status == "active" else pending_goals)
        ),
        "pending_goals": pending_goals,
        "active_count": len(active_goals),
        "pending_count": len(pending_goals),
    }


@router.get("/goals/{goal_id}")
def get_goal(goal_id: int):
    """Get a specific goal"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM goals WHERE id = :id"), {"id": goal_id})
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")

    return {
        "id": row[0],
        "name": row[1],
        "target_per_week": row[2],
        "completed": row[3],
        "last_update": row[4],
    }


@router.put("/goals/{goal_id}")
def update_goal(goal_id: int, goal: Goal):
    """Update a goal"""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            UPDATE goals
            SET name = :name, target_per_week = :target, last_update = :now
            WHERE id = :id
        """
            ),
            {
                "id": goal_id,
                "name": goal.name,
                "target": goal.target_per_week,
                "now": datetime.now(),
            },
        )

    return {"status": "updated", "goal_id": goal_id}


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int):
    """Delete a goal"""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM goals WHERE id = :id"), {"id": goal_id})

    return {"status": "deleted", "goal_id": goal_id}


@router.post("/goals/accept/{goal_id}")
def accept_goal(goal_id: int):
    """
    Accept a pending goal (sets status to 'active').

    Args:
        goal_id: ID of the goal to accept

    Returns:
        {"status": "accepted", "goal_id": int, "goal": dict}
    """
    try:
        # Check if goal exists
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name, status FROM goals WHERE id = :goal_id"), {"goal_id": goal_id}
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

        goal_name, current_status = row

        # Update status to active
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE goals
                    SET status = 'active'
                    WHERE id = :goal_id
                """
                ),
                {"goal_id": goal_id},
            )

        print(f"✅ Goal accepted: {goal_name} (ID: {goal_id}) - {current_status} → active")

        return {
            "status": "accepted",
            "goal_id": goal_id,
            "name": goal_name,
            "previous_status": current_status,
            "new_status": "active",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error accepting goal: {e}")
        raise HTTPException(status_code=500, detail=f"Error accepting goal: {str(e)}")


@router.post("/goals/reject/{goal_id}")
def reject_goal(goal_id: int):
    """
    Reject a pending goal (sets status to 'rejected').

    Args:
        goal_id: ID of the goal to reject

    Returns:
        {"status": "rejected", "goal_id": int, "goal": dict}
    """
    try:
        # Check if goal exists
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name, status FROM goals WHERE id = :goal_id"), {"goal_id": goal_id}
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

        goal_name, current_status = row

        # Update status to rejected
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE goals
                    SET status = 'rejected'
                    WHERE id = :goal_id
                """
                ),
                {"goal_id": goal_id},
            )

        print(f"✅ Goal rejected: {goal_name} (ID: {goal_id}) - {current_status} → rejected")

        return {
            "status": "rejected",
            "goal_id": goal_id,
            "name": goal_name,
            "previous_status": current_status,
            "new_status": "rejected",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error rejecting goal: {e}")
        raise HTTPException(status_code=500, detail=f"Error rejecting goal: {str(e)}")
