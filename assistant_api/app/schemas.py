"""
Pydantic Schemas
================
Request/response models for API validation
"""

from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import List, Optional, Literal, Union
from datetime import date, datetime, time

# Valid types, statuses, and sources
VALID_TYPES = ["appointment", "meeting", "webinar", "deadline", "task", "goal", "session"]
VALID_STATUSES = ["upcoming", "in_progress", "done", "overdue"]
VALID_SOURCES = ["manual", "gmail", "calendar"]


class AssistantItemBase(BaseModel):
    """Base schema with all item fields"""

    type: str
    title: str
    description: Optional[str] = None
    date: date
    start_time: Optional[str] = None  # "HH:MM" format
    end_time: Optional[str] = None  # "HH:MM" format
    status: str = "upcoming"
    source: str = "manual"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        if v not in VALID_SOURCES:
            raise ValueError(f"source must be one of {VALID_SOURCES}")
        return v

    gmail_thread_url: Optional[str] = None
    calendar_event_url: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None  # Will be converted to/from comma-separated string
    priority: Optional[str] = Field(None, pattern="^(low|med|high)$")
    goal_id: Optional[str] = None
    category: Optional[str] = None  # content_creation|trading|education|tech|service|shopping|other
    subcategory: Optional[str] = None  # newsletter|promotional|market_summary|course|mooc|etc
    quadrant: Optional[str] = Field(None, pattern="^(I|II|III|IV)$")  # Eisenhower Matrix


class AssistantItemCreate(AssistantItemBase):
    """Schema for creating new items (no id/timestamps)"""

    pass


class AssistantItemUpdate(BaseModel):
    """Schema for updating items (all fields optional for PATCH)"""

    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    date: Union[date, str, None] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    gmail_thread_url: Optional[str] = None
    calendar_event_url: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None
    priority: Optional[str] = Field(None, pattern="^(low|med|high)$")
    goal_id: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    quadrant: Optional[str] = Field(None, pattern="^(I|II|III|IV)$")  # Eisenhower Matrix

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        if v is not None and v not in VALID_SOURCES:
            raise ValueError(f"source must be one of {VALID_SOURCES}")
        return v


class AssistantItem(AssistantItemBase):
    """Schema for item responses (includes id and timestamps)"""

    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allow ORM model conversion


class ItemListResponse(BaseModel):
    """Schema for paginated list response"""

    items: List[AssistantItem]
    total: int


class StatsSummaryResponse(BaseModel):
    """Schema for dashboard stats"""

    count_by_type: dict
    count_by_status: dict
    today: dict
