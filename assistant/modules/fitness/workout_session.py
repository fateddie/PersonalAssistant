"""
Workout Session Controller (Phase 4)
====================================
Manages workout sessions with timers, rest cues, and exercise logging.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
import json

DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def get_exercises() -> List[Dict[str, Any]]:
    """Get all exercises from the library."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, category, muscle_group, equipment, description
                FROM exercises ORDER BY category, name
            """
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "muscle_group": row[3],
            "equipment": row[4],
            "description": row[5],
        }
        for row in rows
    ]


def get_exercise_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get exercise by name."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, category, muscle_group FROM exercises WHERE name = :name"),
            {"name": name},
        ).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "muscle_group": row[3],
    }


def get_workout_templates() -> List[Dict[str, Any]]:
    """Get all workout templates."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, duration_minutes, difficulty, category, exercises_json
                FROM workout_templates ORDER BY name
            """
            )
        ).fetchall()

    templates = []
    for row in rows:
        exercises = []
        if row[6]:
            try:
                exercises = json.loads(row[6])
            except json.JSONDecodeError:
                exercises = []

        templates.append(
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "duration_minutes": row[3],
                "difficulty": row[4],
                "category": row[5],
                "exercises": exercises,
            }
        )

    return templates


def get_workout_template(template_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific workout template."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, name, description, duration_minutes, difficulty, category, exercises_json
                FROM workout_templates WHERE id = :id
            """
            ),
            {"id": template_id},
        ).fetchone()

    if not row:
        return None

    exercises = []
    if row[6]:
        try:
            exercises = json.loads(row[6])
        except json.JSONDecodeError:
            exercises = []

    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "duration_minutes": row[3],
        "difficulty": row[4],
        "category": row[5],
        "exercises": exercises,
    }


def start_workout_session(template_id: Optional[int] = None) -> int:
    """
    Start a new workout session.

    Args:
        template_id: Optional workout template to follow

    Returns:
        The session ID
    """
    now = datetime.now()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO workout_sessions (template_id, started_at, status)
                VALUES (:template_id, :started, 'in_progress')
            """
            ),
            {
                "template_id": template_id,
                "started": now.isoformat(),
            },
        )

        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def end_workout_session(
    session_id: int,
    overall_rpe: Optional[int] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    End a workout session.

    Args:
        session_id: The session ID
        overall_rpe: Overall rate of perceived exertion (1-10)
        notes: Session notes

    Returns:
        True if successful
    """
    now = datetime.now()

    with engine.begin() as conn:
        # Get session start time
        row = conn.execute(
            text("SELECT started_at FROM workout_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

        if not row:
            return False

        started_at = datetime.fromisoformat(row[0])
        duration = int((now - started_at).total_seconds() / 60)

        result = conn.execute(
            text(
                """
                UPDATE workout_sessions
                SET ended_at = :ended, duration_minutes = :duration,
                    status = 'completed', overall_rpe = :rpe, notes = :notes
                WHERE id = :id
            """
            ),
            {
                "id": session_id,
                "ended": now.isoformat(),
                "duration": duration,
                "rpe": overall_rpe,
                "notes": notes,
            },
        )
        return result.rowcount > 0


def cancel_workout_session(session_id: int) -> bool:
    """Cancel/abandon a workout session."""
    now = datetime.now()

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE workout_sessions
                SET ended_at = :ended, status = 'cancelled'
                WHERE id = :id AND status = 'in_progress'
            """
            ),
            {"id": session_id, "ended": now.isoformat()},
        )
        return result.rowcount > 0


def log_exercise_set(
    session_id: int,
    exercise_id: int,
    set_number: int,
    reps: Optional[int] = None,
    weight_kg: Optional[float] = None,
    duration_seconds: Optional[int] = None,
    rpe: Optional[int] = None,
    notes: Optional[str] = None,
) -> int:
    """
    Log a completed exercise set.

    Args:
        session_id: The workout session ID
        exercise_id: The exercise ID
        set_number: Set number (1, 2, 3, etc.)
        reps: Number of repetitions
        weight_kg: Weight used (if any)
        duration_seconds: Duration for timed exercises
        rpe: Rate of perceived exertion (1-10)
        notes: Optional notes

    Returns:
        The log ID
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO exercise_logs
                (session_id, exercise_id, set_number, reps, weight_kg, duration_seconds, rpe, notes)
                VALUES (:session, :exercise, :set_num, :reps, :weight, :duration, :rpe, :notes)
            """
            ),
            {
                "session": session_id,
                "exercise": exercise_id,
                "set_num": set_number,
                "reps": reps,
                "weight": weight_kg,
                "duration": duration_seconds,
                "rpe": rpe,
                "notes": notes,
            },
        )

        row = conn.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]


def get_session_logs(session_id: int) -> List[Dict[str, Any]]:
    """Get all exercise logs for a session."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT el.id, el.exercise_id, e.name, el.set_number, el.reps,
                       el.weight_kg, el.duration_seconds, el.rpe, el.notes, el.completed_at
                FROM exercise_logs el
                JOIN exercises e ON el.exercise_id = e.id
                WHERE el.session_id = :session_id
                ORDER BY el.completed_at
            """
            ),
            {"session_id": session_id},
        ).fetchall()

    return [
        {
            "id": row[0],
            "exercise_id": row[1],
            "exercise_name": row[2],
            "set_number": row[3],
            "reps": row[4],
            "weight_kg": row[5],
            "duration_seconds": row[6],
            "rpe": row[7],
            "notes": row[8],
            "completed_at": row[9],
        }
        for row in rows
    ]


def get_active_session() -> Optional[Dict[str, Any]]:
    """Get the currently active workout session."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT ws.id, ws.template_id, wt.name, ws.started_at
                FROM workout_sessions ws
                LEFT JOIN workout_templates wt ON ws.template_id = wt.id
                WHERE ws.status = 'in_progress'
                ORDER BY ws.started_at DESC
                LIMIT 1
            """
            )
        ).fetchone()

    if not row:
        return None

    started_at = datetime.fromisoformat(row[3])
    elapsed = (datetime.now() - started_at).total_seconds() / 60

    return {
        "id": row[0],
        "template_id": row[1],
        "template_name": row[2],
        "started_at": row[3],
        "elapsed_minutes": round(elapsed, 1),
    }


def get_recent_sessions(days: int = 7) -> List[Dict[str, Any]]:
    """Get recent workout sessions."""
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT ws.id, ws.template_id, wt.name, ws.started_at, ws.ended_at,
                       ws.duration_minutes, ws.status, ws.overall_rpe
                FROM workout_sessions ws
                LEFT JOIN workout_templates wt ON ws.template_id = wt.id
                WHERE ws.started_at >= :start
                ORDER BY ws.started_at DESC
            """
            ),
            {"start": start_date},
        ).fetchall()

    return [
        {
            "id": row[0],
            "template_id": row[1],
            "template_name": row[2] or "Custom Workout",
            "started_at": row[3],
            "ended_at": row[4],
            "duration_minutes": row[5],
            "status": row[6],
            "overall_rpe": row[7],
        }
        for row in rows
    ]


def get_weekly_stats() -> Dict[str, Any]:
    """Get workout statistics for the current week."""
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    with engine.connect() as conn:
        # Total sessions
        row = conn.execute(
            text(
                """
                SELECT COUNT(*), SUM(duration_minutes), AVG(overall_rpe)
                FROM workout_sessions
                WHERE status = 'completed' AND started_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()

        sessions = row[0] or 0
        total_minutes = row[1] or 0
        avg_rpe = round(row[2], 1) if row[2] else None

        # Total sets
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM exercise_logs el
                JOIN workout_sessions ws ON el.session_id = ws.id
                WHERE ws.started_at >= :week_ago
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()

        total_sets = row[0] or 0

        # Most worked muscle group
        row = conn.execute(
            text(
                """
                SELECT e.muscle_group, COUNT(*) as cnt
                FROM exercise_logs el
                JOIN exercises e ON el.exercise_id = e.id
                JOIN workout_sessions ws ON el.session_id = ws.id
                WHERE ws.started_at >= :week_ago
                GROUP BY e.muscle_group
                ORDER BY cnt DESC
                LIMIT 1
            """
            ),
            {"week_ago": week_ago},
        ).fetchone()

        top_muscle = row[0] if row else None

    return {
        "sessions": sessions,
        "total_minutes": total_minutes,
        "avg_rpe": avg_rpe,
        "total_sets": total_sets,
        "top_muscle_group": top_muscle,
    }


def get_exercise_progress(exercise_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get progress for a specific exercise over time."""
    start_date = (datetime.now() - timedelta(days=days)).isoformat()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT el.completed_at, el.reps, el.weight_kg, el.duration_seconds, el.rpe
                FROM exercise_logs el
                JOIN workout_sessions ws ON el.session_id = ws.id
                WHERE el.exercise_id = :exercise_id
                AND ws.started_at >= :start
                ORDER BY el.completed_at
            """
            ),
            {"exercise_id": exercise_id, "start": start_date},
        ).fetchall()

    return [
        {
            "date": row[0],
            "reps": row[1],
            "weight_kg": row[2],
            "duration_seconds": row[3],
            "rpe": row[4],
        }
        for row in rows
    ]


# RPE-based difficulty adjustment
RPE_GUIDELINES = {
    1: "Very Light - Barely any effort",
    2: "Light - Could do this all day",
    3: "Light - Comfortable",
    4: "Moderate - Starting to feel it",
    5: "Moderate - Challenging but manageable",
    6: "Hard - Requires focus",
    7: "Hard - Difficult, a few reps left",
    8: "Very Hard - Only 2-3 reps left in tank",
    9: "Max Effort - One rep left",
    10: "Maximum - Could not do another rep",
}


def suggest_adjustment(avg_rpe: float) -> str:
    """
    Suggest workout adjustment based on average RPE.

    Args:
        avg_rpe: Average RPE from recent workout

    Returns:
        Suggestion string
    """
    if avg_rpe < 5:
        return "Consider increasing intensity - add reps, sets, or reduce rest time"
    elif avg_rpe < 7:
        return "Good intensity! You're in the optimal training zone"
    elif avg_rpe < 9:
        return "High intensity workout. Make sure to recover well"
    else:
        return "Very high intensity. Consider reducing volume in your next session"
