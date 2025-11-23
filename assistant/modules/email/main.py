"""
Email Module (Phase 2 - Week 1)
================================
Real Gmail IMAP integration with AI-powered summaries and priority detection.

Features:
- Connect to Gmail via IMAP
- Fetch and parse emails (HTML + text)
- Store in database with caching
- Priority detection (HIGH/MEDIUM/LOW)
- OpenAI-powered summarization
- Action item extraction
"""

from typing import Dict, List
from fastapi import APIRouter
from sqlalchemy import text

# Import from split modules
from .database import (
    engine,
    unified_engine,
    get_stored_emails,
    update_email_summary,
)
from .gmail_fetcher import fetch_emails, GMAIL_FETCH_LIMIT
from .classification import store_detected_event

# Import AI service (supports HuggingFace + OpenAI)
from .ai_service import (
    summarize_email,
    extract_action_items,
    generate_daily_email_overview,
    is_configured as ai_is_configured,
    get_provider_status,
)

# Import event detector
from .event_detector import batch_detect_events

router = APIRouter()


def register(app, publish, subscribe):
    """Register email module with the orchestrator"""
    app.include_router(router, prefix="/emails")


@router.get("/summarise")
def summarise_emails(fetch_new: bool = False, limit: int = 10, generate_ai_summary: bool = False):
    """
    Get email summary.

    Query params:
        fetch_new: If True, fetch new emails from Gmail
        limit: Number of emails to return
        generate_ai_summary: If True, generate AI-powered daily overview

    Returns:
        {
            "total": int,
            "by_priority": {"HIGH": int, "MEDIUM": int, "LOW": int},
            "emails": [...],
            "overview": str (if generate_ai_summary=True and OpenAI configured)
        }
    """
    # Fetch new emails if requested
    if fetch_new:
        fetch_emails()

    # Get stored emails
    emails = get_stored_emails(limit=limit)

    # Count by priority
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for email_item in emails:
        priority = email_item.get("priority", "MEDIUM")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    response = {"total": len(emails), "by_priority": priority_counts, "emails": emails}

    # Generate AI overview if requested and configured
    if generate_ai_summary and ai_is_configured():
        overview = generate_daily_email_overview(emails)
        if overview:
            response["overview"] = overview

    return response


@router.get("/fetch")
def fetch_new_emails(limit: int = GMAIL_FETCH_LIMIT):
    """
    Fetch new emails from Gmail.

    Query params:
        limit: Maximum number of emails to fetch

    Returns:
        {
            "fetched": int,
            "message": str
        }
    """
    emails = fetch_emails(limit=limit)

    return {"fetched": len(emails), "message": f"Successfully fetched {len(emails)} new emails"}


@router.post("/generate_summaries")
def generate_summaries_endpoint(limit: int = 10):
    """
    Generate AI summaries for stored emails that don't have summaries yet.

    Query params:
        limit: Maximum number of emails to summarize

    Returns:
        {
            "summarized": int,
            "message": str
        }
    """
    if not ai_is_configured():
        return {
            "summarized": 0,
            "message": "No AI provider configured. Set AI_PROVIDER in config/.env",
        }

    # Get emails without summaries (include body for summarization)
    emails = get_stored_emails(limit=limit, include_body=True)

    # Filter emails that need summaries
    emails_to_summarize = [e for e in emails if not e.get("summary")]

    summarized_count = 0

    print(f"📝 Generating summaries for {len(emails_to_summarize)} emails...")

    for email_data in emails_to_summarize:
        # Generate summary
        summary = summarize_email(email_data)
        if not summary:
            continue

        # Extract action items
        action_items = extract_action_items(email_data)

        # Update database
        if update_email_summary(email_data["email_id"], summary, action_items):
            summarized_count += 1
            print(f"✓ Summarized: {email_data['subject'][:50]}...")

    print(f"✓ Generated {summarized_count} summaries")

    return {
        "summarized": summarized_count,
        "message": f"Successfully generated {summarized_count} AI summaries",
    }


@router.get("/detect-events")
def detect_events_endpoint(limit: int = 50):
    """
    Detect events from stored emails.

    Query params:
        limit: Maximum number of emails to scan

    Returns:
        {
            "detected": int,
            "events": [...],
            "message": str
        }
    """
    # Get recent emails with body text
    emails = get_stored_emails(limit=limit, include_body=True)

    # Detect events
    detected_events = batch_detect_events(emails)

    # Store in database
    stored_count = 0
    for event in detected_events:
        if store_detected_event(event):
            stored_count += 1

    return {
        "detected": stored_count,
        "events": detected_events,
        "message": f"Detected {stored_count} events from {len(emails)} emails",
    }


@router.get("/events")
def get_detected_events(status: str = "all", limit: int = 20, future_only: bool = True):
    """
    Get detected events from unified assistant_items database.

    Query params:
        status: Filter by status (upcoming, in_progress, done, all)
        limit: Maximum number of events to return
        future_only: If True, only return events with date >= today (default: True)

    Returns:
        {
            "events": [...],
            "total": int
        }
    """
    filters = ["source = 'gmail'"]  # Only Gmail events

    # Status filter
    if status != "all":
        filters.append(f"status = '{status}'")

    # Future events only filter
    if future_only:
        filters.append("date >= date('now')")

    where_clause = "WHERE " + " AND ".join(filters)

    with unified_engine.connect() as conn:
        result = conn.execute(
            text(
                f"""
                SELECT id, type, title, date, start_time,
                       location, gmail_thread_url, participants, status
                FROM assistant_items
                {where_clause}
                ORDER BY date ASC
                LIMIT :limit
            """
            ),
            {"limit": limit},
        )

        events = []
        for row in result:
            events.append(
                {
                    "id": row[0],
                    "event_type": row[1],
                    "title": row[2],
                    "date": str(row[3]) if row[3] else None,
                    "start_time": str(row[4]) if row[4] else None,
                    "location": row[5],
                    "url": row[6],
                    "attendees": row[7],
                    "status": row[8],
                }
            )

    return {"events": events, "total": len(events)}


@router.post("/events/{event_id}/approve")
def approve_event(event_id: str):
    """
    Mark event as in_progress (approved for action).

    Args:
        event_id: ID of the assistant_item

    Returns:
        {
            "status": str,
            "message": str
        }
    """
    try:
        with unified_engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE assistant_items
                    SET status = 'in_progress'
                    WHERE id = :event_id
                """
                ),
                {"event_id": event_id},
            )

        return {"status": "approved", "message": f"Event {event_id} marked as in_progress."}

    except Exception as e:
        print(f"❌ Error approving event: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/events/{event_id}/reject")
def reject_event(event_id: str):
    """
    Mark event as done (rejected/dismissed).

    Args:
        event_id: ID of the assistant_item

    Returns:
        {
            "status": str,
            "message": str
        }
    """
    try:
        with unified_engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE assistant_items
                    SET status = 'done'
                    WHERE id = :event_id
                """
                ),
                {"event_id": event_id},
            )

        return {"status": "rejected", "message": f"Event {event_id} marked as done"}

    except Exception as e:
        print(f"❌ Error rejecting event: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/ai-status")
def get_ai_status():
    """
    Get AI provider status (for debugging/transparency).

    Returns:
        {
            "provider_status": {...},
            "message": str
        }
    """
    status = get_provider_status()

    return {"provider_status": status, "message": f"Active provider: {status['active_provider']}"}
