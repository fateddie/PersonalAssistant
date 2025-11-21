"""
Stats Router
============
Dashboard statistics endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=schemas.StatsSummaryResponse)
def get_stats_summary(db: Session = Depends(get_db)):
    """
    Get dashboard statistics

    Returns:
    - count_by_type: Number of items per type
    - count_by_status: Number of items per status
    - today: Stats for items scheduled today
    """
    # Count by type
    type_counts = db.query(
        models.AssistantItem.type,
        func.count(models.AssistantItem.id)
    ).group_by(models.AssistantItem.type).all()

    count_by_type = {str(item_type): count for item_type, count in type_counts}

    # Count by status
    status_counts = db.query(
        models.AssistantItem.status,
        func.count(models.AssistantItem.id)
    ).group_by(models.AssistantItem.status).all()

    count_by_status = {str(status): count for status, count in status_counts}

    # Today's items
    today = date.today()
    today_items = db.query(models.AssistantItem).filter(
        models.AssistantItem.date == today
    ).all()

    today_stats = {
        "total": len(today_items),
        "by_type": {},
        "by_status": {}
    }

    # Group today's items by type and status
    for item in today_items:
        # By type
        type_key = str(item.type)
        today_stats["by_type"][type_key] = today_stats["by_type"].get(type_key, 0) + 1

        # By status
        status_key = str(item.status)
        today_stats["by_status"][status_key] = today_stats["by_status"].get(status_key, 0) + 1

    return {
        "count_by_type": count_by_type,
        "count_by_status": count_by_status,
        "today": today_stats
    }
