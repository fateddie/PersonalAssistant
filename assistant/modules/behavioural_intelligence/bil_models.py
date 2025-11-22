"""
BIL Data Models
===============
Pydantic models for behavioral intelligence.
"""

from pydantic import BaseModel
from typing import Optional


class Goal(BaseModel):
    name: str
    target_per_week: int
    description: Optional[str] = None


class GoalWithCalendar(BaseModel):
    """Goal with optional calendar integration"""
    name: str
    target_per_week: int
    description: Optional[str] = None
    # Calendar fields (all optional)
    recurring_days: Optional[str] = None
    session_time_start: Optional[str] = None
    session_time_end: Optional[str] = None
    weeks_ahead: Optional[int] = 4
    timezone: Optional[str] = None


class SessionLog(BaseModel):
    goal_name: str
    completed: bool
    notes: Optional[str] = None
