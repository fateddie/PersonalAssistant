"""
Behavioural Intelligence Layer (BIL) - Phase 2 & 3.5
====================================================
Goal-reinforcement and conversational data elicitation.

Features:
- Goals CRUD (Create, Read, Update, Delete)
- Session adherence tracking
- Missed session detection
- Adaptive rescheduling suggestions
- Weekly review generator
- Conversational prompt library
- Phase 3.5: Discipline system (evening planning, Eisenhower, habits)
"""

from fastapi import APIRouter

# Initialize database tables on import
from . import bil_db_init  # noqa: F401

# Import sub-routers
from .bil_goals import router as goals_router
from .bil_analytics import router as analytics_router

# Import handlers for scheduler integration
from .bil_handlers import (
    handle_morning_checkin,
    handle_evening_reflection,
    handle_evening_planning,
    handle_morning_fallback,
)

# Re-export models for backward compatibility
from .bil_models import Goal, GoalWithCalendar, SessionLog

# Re-export prompts for backward compatibility
from .bil_prompts import (
    MORNING_PROMPTS,
    EVENING_PROMPTS,
    MISSED_SESSION_PROMPTS,
    ENCOURAGEMENT_PROMPTS,
)

router = APIRouter()

# Include sub-routers
router.include_router(goals_router)
router.include_router(analytics_router)


def register(app, publish, subscribe):
    """Register behavioral intelligence module with orchestrator"""
    app.include_router(router, prefix="/behaviour")

    # Subscribe to scheduled events (original)
    subscribe("morning_checkin", handle_morning_checkin)
    subscribe("evening_reflection", handle_evening_reflection)

    # Phase 3.5: Evening planning and morning fallback
    subscribe("evening_planning", handle_evening_planning)
    subscribe("morning_fallback", handle_morning_fallback)
