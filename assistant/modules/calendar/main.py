"""
Google Calendar Integration Module
===================================
Phase 3 - Calendar & Scheduling

Features:
- OAuth2 authentication with Google Calendar
- Read user's calendars and events
- Create events from detected email events
- Conflict detection
- Two-way sync (future)

Setup Required:
1. Create Google Cloud project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Configure redirect URI: http://localhost:8000/calendar/oauth/callback
5. Add credentials to config/.env
"""

from fastapi import APIRouter

from .calendar_config import GOOGLE_CALENDAR_ENABLED
from .calendar_oauth import router as oauth_router
from .calendar_events import router as events_router
from .calendar_goal_events import router as goal_events_router

# Re-export for backward compatibility
from .calendar_service import get_calendar_service
from .calendar_events import create_event

router = APIRouter()

# Include sub-routers
router.include_router(oauth_router)
router.include_router(events_router)
router.include_router(goal_events_router)


def register(app, publish, subscribe):
    """Register calendar module with the orchestrator"""
    app.include_router(router, prefix="/calendar")
    print(f"📅 Calendar module loaded (enabled: {GOOGLE_CALENDAR_ENABLED})")
