"""
Calendar Goal Events
====================
Create calendar events from goals and detected emails.
"""

from datetime import datetime, date
from typing import Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .calendar_config import engine
from .calendar_service import get_calendar_service
from .calendar_events import create_event

router = APIRouter()


@router.post("/events/create-recurring-for-goal")
def create_recurring_events_for_goal(goal_id: int):
    """Create recurring calendar events for a goal with calendar config."""
    from assistant.modules.calendar.helpers import generate_event_dates

    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM goals WHERE id = :goal_id"), {"goal_id": goal_id}
        )
        goal_row = result.fetchone()
        if not goal_row:
            raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
        goal_name = goal_row[0]

        result = conn.execute(
            text(
                """
                SELECT recurring_days, session_time_start, session_time_end, weeks_ahead, is_active
                FROM goal_calendar_config
                WHERE goal_id = :goal_id AND is_active = 1
            """
            ),
            {"goal_id": goal_id},
        )
        config_row = result.fetchone()
        if not config_row:
            raise HTTPException(
                status_code=404, detail=f"No active calendar config found for goal {goal_id}"
            )

        recurring_days, time_start, time_end, weeks_ahead, is_active = config_row

    days_list = recurring_days.split(",")
    today = date.today()
    event_dates = generate_event_dates(today, days_list, num_weeks=weeks_ahead)

    if not event_dates:
        return {
            "events_created": 0,
            "event_ids": [],
            "message": "No events to create (no matching dates in time window)",
        }

    created_events = []
    for event_date in event_dates:
        try:
            start_datetime = datetime.combine(
                event_date, datetime.strptime(time_start, "%H:%M").time()
            )
            end_datetime = datetime.combine(event_date, datetime.strptime(time_end, "%H:%M").time())

            event = {
                "summary": f"{goal_name} Session",
                "description": f"Recurring session for goal: {goal_name}",
                "start": {"dateTime": start_datetime.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_datetime.isoformat(), "timeZone": "UTC"},
                "reminders": {"useDefault": True},
            }

            created_event = service.events().insert(calendarId="primary", body=event).execute()
            event_id = created_event["id"]

            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO goal_calendar_events (goal_id, calendar_event_id, event_date) VALUES (:goal_id, :calendar_event_id, :event_date)"
                    ),
                    {"goal_id": goal_id, "calendar_event_id": event_id, "event_date": event_date},
                )

            created_events.append(event_id)
            print(f"✅ Created calendar event for {goal_name} on {event_date}")

        except Exception as e:
            print(f"❌ Failed to create event for {event_date}: {str(e)}")

    return {
        "events_created": len(created_events),
        "event_ids": created_events,
        "message": f"✅ Created {len(created_events)} calendar events for '{goal_name}'",
    }


@router.post("/events/create-from-detected/{event_id}")
def create_event_from_detected(event_id: int):
    """Create Google Calendar event from a detected email event."""
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT title, date_time, location, url, attendees, approval_status FROM detected_events WHERE id = :event_id"
            ),
            {"event_id": event_id},
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Detected event {event_id} not found")

        title, date_time, location, url, attendees, approval_status = row

        if approval_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Event must be approved first. Use POST /emails/events/{id}/approve",
            )

    event_data = {"summary": title, "start_time": date_time}

    if location:
        event_data["location"] = location

    description_parts = []
    if url:
        description_parts.append(f"Link: {url}")
    if attendees:
        description_parts.append(f"Attendees: {attendees}")
    if description_parts:
        event_data["description"] = "\n".join(description_parts)

    try:
        result = create_event(event_data)

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO calendar_events (google_event_id, title, start_time, end_time, location, url, source, detected_event_id)
                    VALUES (:google_id, :title, :start_time, :end_time, :location, :url, 'detected_email', :detected_id)
                """
                ),
                {
                    "google_id": result["event_id"],
                    "title": title,
                    "start_time": date_time,
                    "end_time": None,
                    "location": location,
                    "url": url,
                    "detected_id": event_id,
                },
            )

        print(f"✅ Created calendar event from detected event #{event_id}")

        return {
            "calendar_event_id": result["event_id"],
            "google_event_id": result["event_id"],
            "html_link": result.get("html_link"),
            "message": f"Event added to Google Calendar: {title}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating calendar event: {str(e)}")
