"""
Calendar Actions
================
Calendar-related action functions.
"""

import requests
from datetime import date
from typing import Dict


def create_calendar_event(title: str, event_date: date, start_time: str, end_time: str) -> bool:
    """Create a Google Calendar event via the orchestrator API."""
    try:
        start_dt = f"{event_date}T{start_time}:00"
        end_dt = f"{event_date}T{end_time}:00"

        response = requests.post(
            "http://localhost:8000/calendar/events/create",
            json={"summary": title, "start_time": start_dt, "end_time": end_dt},
            timeout=10
        )
        if response.status_code != 200:
            print(f"⚠️ Calendar API returned {response.status_code}: {response.text[:100]}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("⚠️ Calendar creation failed: Orchestrator not running at localhost:8000")
        return False
    except Exception as e:
        print(f"⚠️ Calendar creation failed: {str(e)}")
        return False


def list_calendar_events(pending_data: Dict) -> str:
    """List upcoming calendar events."""
    try:
        max_results = pending_data.get('max_results', 10)
        response = requests.get(
            "http://localhost:8000/calendar/events",
            params={"max_results": max_results},
            timeout=10
        )

        if response.status_code != 200:
            return "❌ Couldn't fetch calendar. Is calendar authenticated?"

        data = response.json()
        events = data.get('events', [])

        if not events:
            return "📭 No upcoming events on your calendar."

        parts = [f"📅 **Upcoming {len(events)} events:**\n"]
        for event in events:
            summary = event.get('summary', 'No title')
            start = event.get('start', '')[:16]
            eid = event.get('id', '')[:15]
            parts.append(f"• **{summary}**")
            parts.append(f"  {start} | ID: `{eid}...`")

        return "\n".join(parts)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_calendar_status() -> str:
    """Get calendar connection status."""
    try:
        response = requests.get("http://localhost:8000/calendar/status", timeout=5)

        if response.status_code != 200:
            return "❌ Calendar service not available."

        data = response.json()
        enabled = data.get('enabled', False)
        authenticated = data.get('authenticated', False)

        if not enabled:
            return "⚠️ Google Calendar is disabled. Set GOOGLE_CALENDAR_ENABLED=true in config/.env"
        if not authenticated:
            return "⚠️ Google Calendar not authenticated. Visit http://localhost:8000/calendar/auth"

        return "✅ Google Calendar is connected and authenticated."

    except Exception as e:
        return f"❌ Error: {str(e)}"


def check_calendar_conflicts(pending_data: Dict) -> str:
    """Check for calendar conflicts."""
    start_time = pending_data.get('start_time')
    end_time = pending_data.get('end_time')

    if not start_time or not end_time:
        return "❌ Need start_time and end_time to check conflicts."

    try:
        response = requests.get(
            "http://localhost:8000/calendar/conflicts",
            params={"start_time": start_time, "end_time": end_time},
            timeout=10
        )

        if response.status_code != 200:
            return "❌ Error checking conflicts."

        data = response.json()
        has_conflict = data.get('has_conflict', False)
        conflicts = data.get('conflicting_events', [])

        if not has_conflict:
            return "✅ No conflicts - time slot is free!"

        parts = [f"⚠️ **{len(conflicts)} conflicting events:**\n"]
        for event in conflicts:
            summary = event.get('summary', 'No title')
            start = event.get('start', '')
            parts.append(f"• {summary} at {start}")

        return "\n".join(parts)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def hide_calendar_event(pending_data: Dict) -> str:
    """Hide a calendar event."""
    event_id = pending_data.get('event_id')
    if not event_id:
        return "❌ No event ID provided."

    try:
        response = requests.post(
            f"http://localhost:8000/calendar/events/hide/{event_id}",
            timeout=10
        )

        if response.status_code == 200:
            return "✅ Event hidden from display."
        return "❌ Failed to hide event."

    except Exception as e:
        return f"❌ Error: {str(e)}"


def delete_calendar_event_action(pending_data: Dict) -> str:
    """Delete calendar event(s) from Google Calendar by ID or title."""
    event_ids = pending_data.get('event_ids', [])
    event_id = pending_data.get('event_id')
    event_title = pending_data.get('event_title')

    # If title is provided, search for matching events first
    if event_title and not event_ids and not event_id:
        try:
            response = requests.get(
                "http://localhost:8000/calendar/events",
                params={"max_results": 100},
                timeout=10
            )
            if response.status_code == 200:
                events = response.json().get('events', [])
                matching_ids = [
                    event.get('id') for event in events
                    if event_title.lower() in event.get('summary', '').lower()
                ]
                event_ids = matching_ids
                if not event_ids:
                    return f"❌ No calendar events found matching '{event_title}'"
            else:
                return f"❌ Failed to search calendar: {response.text[:50]}"
        except Exception as e:
            return f"❌ Error searching calendar: {str(e)}"

    if event_id and not event_ids:
        event_ids = [event_id]

    if not event_ids:
        return "❌ No event ID(s) provided."

    deleted = 0
    failed = 0

    for eid in event_ids:
        try:
            response = requests.delete(f"http://localhost:8000/calendar/events/{eid}", timeout=10)
            if response.status_code == 200:
                deleted += 1
            else:
                failed += 1
                print(f"⚠️ Failed to delete {eid}: {response.text[:50]}")
        except Exception as e:
            failed += 1
            print(f"⚠️ Error deleting {eid}: {str(e)}")

    if failed == 0:
        return f"✅ Deleted {deleted} calendar event(s)."
    elif deleted > 0:
        return f"✅ Deleted {deleted} events, ❌ {failed} failed."
    else:
        return "❌ Failed to delete events."
