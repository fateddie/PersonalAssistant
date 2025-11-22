"""
Behavioural Intelligence Layer (BIL) - Phase 2
==============================================
Goal-reinforcement and conversational data elicitation.

Features:
- Goals CRUD (Create, Read, Update, Delete)
- Session adherence tracking
- Missed session detection
- Adaptive rescheduling suggestions
- Weekly review generator
- Conversational prompt library
"""

from fastapi import APIRouter

# Import sub-routers
from .bil_goals import router as goals_router
from .bil_analytics import router as analytics_router

# Import handlers for scheduler integration
from .bil_handlers import handle_morning_checkin, handle_evening_reflection

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

    # Subscribe to scheduled events
    subscribe("morning_checkin", handle_morning_checkin)
    subscribe("evening_reflection", handle_evening_reflection)
