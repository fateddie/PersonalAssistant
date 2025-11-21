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
    appointment = "appointment"
    meeting = "meeting"
    task = "task"
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
    Unified model for appointments, meetings, tasks, and goals
    All 4 types share this schema with type-specific field usage
    """
    __tablename__ = "assistant_items"

    # Core fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(ItemType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Temporal fields
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Status tracking
    status = Column(Enum(ItemStatus), nullable=False, default=ItemStatus.upcoming)
    source = Column(Enum(ItemSource), nullable=False, default=ItemSource.manual)

    # External links
    gmail_thread_url = Column(String, nullable=True)
    calendar_event_url = Column(String, nullable=True)

    # Additional metadata
    location = Column(String(255), nullable=True)
    participants = Column(Text, nullable=True)  # Comma-separated emails
    priority = Column(String(10), nullable=True)  # low|med|high
    goal_id = Column(String, nullable=True)  # Link tasks to goals

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
