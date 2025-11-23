"""
Database Models
===============
SQLAlchemy models for unified item storage
"""

from sqlalchemy import Column, String, Date, Time, Enum, DateTime, Text
from sqlalchemy.sql import func
import uuid
import enum

from .db import Base


class ItemType(str, enum.Enum):
    """Type of assistant item"""

    # Personal appointments (doctor, dentist, haircut, etc.)
    appointment = "appointment"
    # Actual meetings you need to attend
    meeting = "meeting"
    # Marketing webinars, promotional events, newsletters
    webinar = "webinar"
    # Due dates, expiration notices
    deadline = "deadline"
    # Tasks to complete
    task = "task"
    # Long-term goals
    goal = "goal"


class ItemStatus(str, enum.Enum):
    """Status of assistant item"""

    upcoming = "upcoming"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"


class ItemSource(str, enum.Enum):
    """Source where item was created"""

    manual = "manual"
    gmail = "gmail"
    calendar = "calendar"


class AssistantItem(Base):
    """
    Unified model for appointments, meetings, tasks, goals, webinars, deadlines
    All types share this schema with type-specific field usage
    """

    __tablename__ = "assistant_items"

    # Core fields - ID is set by crud.py's _generate_sequential_id()
    id = Column(String, primary_key=True)
    # Use String instead of Enum for flexibility with new types
    type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Temporal fields
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Status tracking (use String for flexibility)
    status = Column(String(20), nullable=False, default="upcoming")
    source = Column(String(20), nullable=False, default="manual")

    # External links
    gmail_thread_url = Column(String, nullable=True)
    calendar_event_url = Column(String, nullable=True)

    # Additional metadata
    location = Column(String(255), nullable=True)
    participants = Column(Text, nullable=True)  # Comma-separated emails
    priority = Column(String(10), nullable=True)  # low|med|high
    goal_id = Column(String, nullable=True)  # Link tasks to goals

    # Email categorization
    category = Column(
        String(50), nullable=True
    )  # content_creation|trading|education|tech|service|shopping|other
    subcategory = Column(
        String(50), nullable=True
    )  # newsletter|promotional|market_summary|course|mooc|etc

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
