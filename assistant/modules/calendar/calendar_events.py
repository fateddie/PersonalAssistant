"""
Calendar Events
===============
CRUD operations for Google Calendar events.
"""

from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .calendar_config import engine, GOOGLE_CALENDAR_ENABLED
from .calendar_service import get_calendar_service

router = APIRouter()


@router.get("/calendars")
def list_calendars():
    """List user's Google Calendars."""
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    try:
        calendar_list = service.calendarList().list().execute()
        calendars = []

        for cal in calendar_list.get('items', []):
            calendars.append({
                "id": cal['id'],
                "summary": cal['summary'],
                "primary": cal.get('primary', False),
                "time_zone": cal.get('timeZone', 'UTC')
            })

        return {"calendars": calendars}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendars: {str(e)}")


@router.get("/events")
def list_events(
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: str = None,
    time_max: str = None
):
    """List upcoming events from Google Calendar."""
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    try:
        if not time_min:
            time_min = datetime.utcnow().isoformat() + 'Z'

        if not time_max:
            three_months_later = datetime.utcnow() + timedelta(days=90)
            time_max = three_months_later.isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Get list of hidden event IDs
        hidden_event_ids = set()
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT google_event_id FROM hidden_calendar_events"))
                hidden_event_ids = {row[0] for row in result}
        except Exception:
            pass

        events = []
        for event in events_result.get('items', []):
            event_id = event['id']
            if event_id in hidden_event_ids:
                continue

            start = event['start'].get('dateTime', event['start'].get('date'))
            events.append({
                "id": event_id,
                "summary": event.get('summary', 'No title'),
                "start": start,
                "end": event['end'].get('dateTime', event['end'].get('date')),
                "location": event.get('location'),
                "description": event.get('description')
            })

        return {"events": events}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")


@router.post("/events/create")
def create_event(event_data: Dict):
    """Create a new calendar event."""
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    if 'summary' not in event_data or 'start_time' not in event_data:
        raise HTTPException(status_code=400, detail="summary and start_time are required")

    try:
        start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))

        if 'end_time' in event_data:
            end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
        else:
            end_time = start_time + timedelta(hours=1)

        event = {
            'summary': event_data['summary'],
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
        }

        if event_data.get('location'):
            event['location'] = event_data['location']
        if event_data.get('description'):
            event['description'] = event_data['description']

        if event_data.get('reminders'):
            event['reminders'] = {'useDefault': False, 'overrides': event_data['reminders']}
        else:
            event['reminders'] = {'useDefault': True}

        calendar_id = event_data.get('calendar_id', 'primary')
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()

        print(f"✅ Created calendar event: {event_data['summary']}")

        return {
            "event_id": created_event['id'],
            "html_link": created_event.get('htmlLink'),
            "message": f"Event '{event_data['summary']}' created successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")


@router.get("/conflicts")
def check_conflicts(start_time: str, end_time: str, calendar_id: str = "primary"):
    """Check for conflicts in calendar for a given time range."""
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        conflicting_events = []
        for event in events_result.get('items', []):
            conflicting_events.append({
                "summary": event.get('summary', 'No title'),
                "start": event['start'].get('dateTime', event['start'].get('date')),
                "end": event['end'].get('dateTime', event['end'].get('date'))
            })

        return {"has_conflict": len(conflicting_events) > 0, "conflicting_events": conflicting_events}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking conflicts: {str(e)}")


@router.post("/events/hide/{google_event_id}")
def hide_calendar_event(google_event_id: str):
    """Hide a calendar event from display."""
    try:
        service = get_calendar_service()
        event_title = "Unknown Event"

        if service:
            try:
                event = service.events().get(calendarId='primary', eventId=google_event_id).execute()
                event_title = event.get('summary', 'Unknown Event')
            except Exception:
                pass

        with engine.begin() as conn:
            conn.execute(
                text("INSERT OR IGNORE INTO hidden_calendar_events (google_event_id, event_title) VALUES (:event_id, :title)"),
                {"event_id": google_event_id, "title": event_title}
            )

        print(f"✅ Calendar event hidden: {event_title} (ID: {google_event_id})")
        return {"status": "hidden", "event_id": google_event_id, "event_title": event_title, "message": f"Event '{event_title}' hidden from display"}

    except Exception as e:
        print(f"❌ Error hiding calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Error hiding event: {str(e)}")


@router.post("/events/unhide/{google_event_id}")
def unhide_calendar_event(google_event_id: str):
    """Unhide a previously hidden calendar event."""
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM hidden_calendar_events WHERE google_event_id = :event_id"), {"event_id": google_event_id})

        print(f"✅ Calendar event unhidden (ID: {google_event_id})")
        return {"status": "unhidden", "event_id": google_event_id, "message": "Event will now be visible"}

    except Exception as e:
        print(f"❌ Error unhiding calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Error unhiding event: {str(e)}")


@router.get("/events/hidden")
def list_hidden_events():
    """List all hidden calendar events."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT google_event_id, event_title, hidden_at FROM hidden_calendar_events ORDER BY hidden_at DESC"))
            hidden_events = [{"google_event_id": row[0], "title": row[1], "hidden_at": row[2]} for row in result]

        return {"hidden_events": hidden_events}

    except Exception as e:
        print(f"❌ Error listing hidden events: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing hidden events: {str(e)}")


@router.delete("/events/{google_event_id}")
def delete_calendar_event(google_event_id: str):
    """Delete a calendar event from Google Calendar."""
    if not GOOGLE_CALENDAR_ENABLED:
        raise HTTPException(status_code=400, detail="Google Calendar is disabled")

    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Calendar not authenticated")

    try:
        service.events().delete(calendarId='primary', eventId=google_event_id).execute()
        print(f"✅ Deleted calendar event (ID: {google_event_id})")
        return {"status": "deleted", "event_id": google_event_id, "message": "Event deleted from Google Calendar"}

    except Exception as e:
        print(f"❌ Error deleting calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")
