"""
Fitness API Router (Phase 4)
============================
Endpoints for workout sessions, exercise logging, and progress tracking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.fitness.workout_session import (
    get_exercises,
    get_exercise_by_name,
    get_workout_templates,
    get_workout_template,
    start_workout_session,
    end_workout_session,
    cancel_workout_session,
    log_exercise_set,
    get_session_logs,
    get_active_session,
    get_recent_sessions,
    get_weekly_stats,
    get_exercise_progress,
    suggest_adjustment,
)

router = APIRouter(prefix="/fitness", tags=["fitness"])


# ============ Pydantic Models ============


class ExerciseSetLog(BaseModel):
    """Log an exercise set."""

    exercise_id: int
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_seconds: Optional[int] = None
    rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class EndSessionRequest(BaseModel):
    """End workout session request."""

    overall_rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


# ============ Exercise Endpoints ============


@router.get("/exercises")
async def list_exercises():
    """Get all exercises in the library."""
    exercises = get_exercises()
    return {"exercises": exercises}


@router.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: int):
    """Get a specific exercise by ID."""
    exercises = get_exercises()
    for ex in exercises:
        if ex["id"] == exercise_id:
            return ex
    raise HTTPException(status_code=404, detail="Exercise not found")


# ============ Workout Template Endpoints ============


@router.get("/templates")
async def list_templates():
    """Get all workout templates."""
    templates = get_workout_templates()
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(template_id: int):
    """Get a specific workout template."""
    template = get_workout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ============ Session Endpoints ============


@router.post("/sessions/start")
async def start_session(template_id: Optional[int] = None):
    """
    Start a new workout session.

    Args:
        template_id: Optional template to follow
    """
    # Check for existing active session
    active = get_active_session()
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"Session {active['id']} already in progress. End it first.",
        )

    session_id = start_workout_session(template_id)

    response = {
        "session_id": session_id,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
    }

    if template_id:
        template = get_workout_template(template_id)
        if template:
            response["template"] = template

    return response


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: int, request: EndSessionRequest):
    """End a workout session."""
    success = end_workout_session(session_id, request.overall_rpe, request.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or already ended")

    # Get suggestion based on RPE
    suggestion = None
    if request.overall_rpe:
        suggestion = suggest_adjustment(request.overall_rpe)

    return {"success": True, "session_id": session_id, "suggestion": suggestion}


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: int):
    """Cancel a workout session."""
    success = cancel_workout_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or not in progress")
    return {"success": True, "session_id": session_id}


@router.get("/sessions/active")
async def get_current_session():
    """Get the currently active workout session."""
    session = get_active_session()
    if not session:
        return {"has_active_session": False}
    return {"has_active_session": True, "session": session}


@router.get("/sessions/recent")
async def list_recent_sessions(days: int = 7):
    """Get recent workout sessions."""
    sessions = get_recent_sessions(days)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/logs")
async def get_session_exercise_logs(session_id: int):
    """Get all exercise logs for a session."""
    logs = get_session_logs(session_id)
    return {"logs": logs}


# ============ Exercise Logging Endpoints ============


@router.post("/sessions/{session_id}/log")
async def log_set(session_id: int, log: ExerciseSetLog):
    """Log an exercise set during a workout session."""
    # Verify session is active
    active = get_active_session()
    if not active or active["id"] != session_id:
        raise HTTPException(status_code=400, detail="Session not active")

    log_id = log_exercise_set(
        session_id=session_id,
        exercise_id=log.exercise_id,
        set_number=log.set_number,
        reps=log.reps,
        weight_kg=log.weight_kg,
        duration_seconds=log.duration_seconds,
        rpe=log.rpe,
        notes=log.notes,
    )

    return {"success": True, "log_id": log_id}


# ============ Stats & Progress Endpoints ============


@router.get("/stats/weekly")
async def weekly_stats():
    """Get workout statistics for the current week."""
    stats = get_weekly_stats()
    return stats


@router.get("/progress/{exercise_id}")
async def exercise_progress(exercise_id: int, days: int = 30):
    """Get progress for a specific exercise."""
    progress = get_exercise_progress(exercise_id, days)
    return {"exercise_id": exercise_id, "progress": progress}
