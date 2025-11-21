"""
Pydantic Schemas
================
Request/response models for API validation
"""
from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional
from datetime import date, datetime, time

from .models import ItemType, ItemStatus, ItemSource


class AssistantItemBase(BaseModel):
    """Base schema with all item fields"""
    type: ItemType
    title: str
    description: Optional[str] = None
    date: date
    start_time: Optional[str] = None  # "HH:MM" format
    end_time: Optional[str] = None    # "HH:MM" format
    status: ItemStatus = ItemStatus.upcoming
    source: ItemSource = ItemSource.manual
    gmail_thread_url: Optional[str] = None
    calendar_event_url: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None  # Will be converted to/from comma-separated string
    priority: Optional[str] = Field(None, pattern="^(low|med|high)$")
    goal_id: Optional[str] = None


class AssistantItemCreate(AssistantItemBase):
    """Schema for creating new items (no id/timestamps)"""
    pass


class AssistantItemUpdate(BaseModel):
    """Schema for updating items (all fields optional for PATCH)"""
    type: Optional[ItemType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[ItemStatus] = None
    source: Optional[ItemSource] = None
    gmail_thread_url: Optional[str] = None
    calendar_event_url: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None
    priority: Optional[str] = Field(None, pattern="^(low|med|high)$")
    goal_id: Optional[str] = None


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
