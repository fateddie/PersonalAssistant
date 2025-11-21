"""
CRUD Operations
===============
Database operations for assistant items
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from datetime import date

from . import models, schemas
from datetime import time as time_type


def _convert_db_item(item: models.AssistantItem) -> models.AssistantItem:
    """Convert DB types for Pydantic serialization"""
    # Convert time objects to strings
    if item.start_time and isinstance(item.start_time, time_type):
        item.start_time = item.start_time.strftime("%H:%M")
    if item.end_time and isinstance(item.end_time, time_type):
        item.end_time = item.end_time.strftime("%H:%M")

    # Convert participants string to list
    if item.participants and isinstance(item.participants, str):
        item.participants = [p.strip() for p in item.participants.split(",") if p.strip()]

    return item


def get_items(
    db: Session,
    type_filter: Optional[List[str]] = None,
    status_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[models.AssistantItem], int]:
    """
    Get items with optional filtering and pagination

    Returns: (items, total_count)
    """
    query = db.query(models.AssistantItem)

    # Apply filters
    if type_filter:
        query = query.filter(models.AssistantItem.type.in_(type_filter))

    if status_filter:
        query = query.filter(models.AssistantItem.status == status_filter)

    if source_filter:
        query = query.filter(models.AssistantItem.source == source_filter)

    if date_from:
        query = query.filter(models.AssistantItem.date >= date_from)

    if date_to:
        query = query.filter(models.AssistantItem.date <= date_to)

    if search:
        # Full-text search across multiple fields
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.AssistantItem.title.ilike(search_pattern),
                models.AssistantItem.description.ilike(search_pattern),
                models.AssistantItem.location.ilike(search_pattern),
                models.AssistantItem.participants.ilike(search_pattern)
            )
        )

    # Get total before pagination
    total = query.count()

    # Apply pagination and ordering
    items = query.order_by(
        models.AssistantItem.date.asc(),
        models.AssistantItem.start_time.asc()
    ).offset(offset).limit(limit).all()

    # Convert DB types
    items = [_convert_db_item(item) for item in items]

    return items, total


def get_item(db: Session, item_id: str) -> Optional[models.AssistantItem]:
    """Get single item by ID"""
    item = db.query(models.AssistantItem).filter(
        models.AssistantItem.id == item_id
    ).first()
    return _convert_db_item(item) if item else None


def create_item(
    db: Session,
    item: schemas.AssistantItemCreate
) -> models.AssistantItem:
    """Create new item"""
    # Convert participants list to comma-separated string
    item_dict = item.model_dump()
    if item_dict.get("participants"):
        item_dict["participants"] = ",".join(item_dict["participants"])

    db_item = models.AssistantItem(**item_dict)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _convert_db_item(db_item)


def update_item(
    db: Session,
    item_id: str,
    item_update: schemas.AssistantItemUpdate
) -> Optional[models.AssistantItem]:
    """Update existing item"""
    db_item = get_item(db, item_id)
    if not db_item:
        return None

    # Get update data (exclude unset fields)
    update_data = item_update.model_dump(exclude_unset=True)

    # Convert participants list to comma-separated string
    if "participants" in update_data and update_data["participants"]:
        update_data["participants"] = ",".join(update_data["participants"])

    # Apply updates
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return _convert_db_item(db_item)


def delete_item(db: Session, item_id: str) -> bool:
    """Delete item by ID"""
    db_item = get_item(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True
