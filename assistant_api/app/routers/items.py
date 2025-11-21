"""
Items Router
============
CRUD endpoints for assistant items
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import crud, schemas
from ..db import get_db

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=schemas.ItemListResponse)
def list_items(
    type: Optional[List[str]] = Query(None),
    status: Optional[str] = None,
    source: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List items with optional filtering

    - **type**: Filter by item type(s) - can specify multiple
    - **status**: Filter by status (upcoming/in_progress/done/overdue)
    - **source**: Filter by source (manual/gmail/calendar)
    - **date_from**: Filter items from this date onwards
    - **date_to**: Filter items up to this date
    - **search**: Full-text search across title, description, location, participants
    - **limit**: Number of items to return (1-100, default 50)
    - **offset**: Number of items to skip (for pagination)
    """
    items, total = crud.get_items(
        db=db,
        type_filter=type,
        status_filter=status,
        source_filter=source,
        date_from=date_from,
        date_to=date_to,
        search=search,
        limit=limit,
        offset=offset
    )
    return {"items": items, "total": total}


@router.get("/{item_id}", response_model=schemas.AssistantItem)
def get_item(item_id: str, db: Session = Depends(get_db)):
    """Get single item by ID"""
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("", response_model=schemas.AssistantItem, status_code=201)
def create_item(item: schemas.AssistantItemCreate, db: Session = Depends(get_db)):
    """Create new item"""
    return crud.create_item(db, item)


@router.patch("/{item_id}", response_model=schemas.AssistantItem)
def update_item(
    item_id: str,
    item_update: schemas.AssistantItemUpdate,
    db: Session = Depends(get_db)
):
    """Update existing item (partial update)"""
    updated_item = crud.update_item(db, item_id, item_update)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: str, db: Session = Depends(get_db)):
    """Delete item by ID"""
    success = crud.delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return None
