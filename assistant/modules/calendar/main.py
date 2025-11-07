"""
Google Calendar Integration Module
===================================
Phase 3 - Calendar & Scheduling

Features:
- OAuth2 authentication with Google Calendar
- Read user's calendars and events
- Create events from detected email events
- Conflict detection
- Two-way sync (future)

Setup Required:
1. Create Google Cloud project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Configure redirect URI: http://localhost:8000/calendar/oauth/callback
5. Add credentials to config/.env
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
config_dir = Path(__file__).parent.parent.parent.parent / "config" / ".env"
load_dotenv(config_dir)

router = APIRouter()

# Database connection
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///assistant/data/memory.db")
engine = create_engine(DB_PATH.replace("sqlite:///", "sqlite:///"))

# Google Calendar configuration
GOOGLE_CALENDAR_ENABLED = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/calendar/oauth/callback")

# OAuth token storage
TOKEN_FILE = Path(__file__).parent.parent.parent.parent / "config" / "google_calendar_token.json"

# Google Calendar API client (initialized on first use)
calendar_service = None


def register(app, publish, subscribe):
    """Register calendar module with the orchestrator"""
    app.include_router(router, prefix="/calendar")
    print(f"📅 Calendar module loaded (enabled: {GOOGLE_CALENDAR_ENABLED})")


def get_calendar_service():
    """
    Get or initialize Google Calendar service.

    Returns:
        Google Calendar service object or None if not configured
    """
    global calendar_service

    if not GOOGLE_CALENDAR_ENABLED:
        return None

    if calendar_service is not None:
        return calendar_service

    # Check if we have credentials
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        print("⚠️  Google Calendar not configured. See docs/CALENDAR_SETUP.md")
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        creds = None

        # Load token if exists
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as token:
                creds_data = json.load(token)
                creds = Credentials.from_authorized_user_info(creds_data)

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        if creds and creds.valid:
            calendar_service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar service initialized")
            return calendar_service

        # Need to authenticate
        print("⚠️  Google Calendar authentication required. Visit /calendar/auth")
        return None

    except ImportError:
        print("⚠️  google-api-python-client not installed. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
        return None
    except Exception as e:
        print(f"❌ Error initializing Google Calendar: {e}")
        return None


@router.get("/auth")
def start_oauth_flow():
    """
    Start OAuth2 authentication flow.

    Redirects user to Google consent screen.
    """
    if not GOOGLE_CALENDAR_ENABLED:
        return {"error": "Google Calendar integration is disabled. Set GOOGLE_CALENDAR_ENABLED=true in config/.env"}

    try:
        from google_auth_oauthlib.flow import Flow

        # Create flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar']
        )

        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )

        return RedirectResponse(url=authorization_url)

    except ImportError:
        raise HTTPException(status_code=500, detail="google-auth-oauthlib not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth flow error: {str(e)}")


@router.get("/oauth/callback")
def oauth_callback(code: str = Query(...), state: str = Query(None)):
    """
    OAuth2 callback endpoint.

    Google redirects here after user grants permission.
    """
    try:
        from google_auth_oauthlib.flow import Flow

        # Create flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar'],
            state=state
        )

        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # Exchange code for token
        flow.fetch_token(code=code)

        # Save credentials
        creds = flow.credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print("✅ Google Calendar authentication successful")

        return {
            "status": "success",
            "message": "Google Calendar connected! You can now create events.",
            "expires_at": creds.expiry.isoformat() if creds.expiry else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/status")
def get_calendar_status():
    """
    Get Google Calendar connection status.

    Returns:
        {
            "enabled": bool,
            "authenticated": bool,
            "token_expires": str or None
        }
    """
    authenticated = False
    token_expires = None

    if GOOGLE_CALENDAR_ENABLED and TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r') as token:
                creds_data = json.load(token)
                authenticated = True
                token_expires = creds_data.get('expiry')
        except:
            pass

    return {
        "enabled": GOOGLE_CALENDAR_ENABLED,
        "authenticated": authenticated,
        "token_expires": token_expires,
        "setup_url": "/calendar/auth" if not authenticated else None
    }


@router.get("/calendars")
def list_calendars():
    """
    List user's Google Calendars.

    Returns:
        {
            "calendars": [
                {
                    "id": str,
                    "summary": str,
                    "primary": bool,
                    "time_zone": str
                }
            ]
        }
    """
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
    time_min: str = None
):
    """
    List upcoming events from Google Calendar.

    Query params:
        calendar_id: Calendar ID (default: "primary")
        max_results: Maximum number of events to return
        time_min: ISO format datetime (default: now)

    Returns:
        {
            "events": [...]
        }
    """
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    try:
        if not time_min:
            time_min = datetime.utcnow().isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = []
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime', event['start'].get('date'))
            events.append({
                "id": event['id'],
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
    """
    Create a new calendar event.

    Body:
        {
            "summary": str (required),
            "start_time": str ISO format (required),
            "end_time": str ISO format (optional, defaults to start + 1 hour),
            "location": str (optional),
            "description": str (optional),
            "calendar_id": str (optional, defaults to "primary")
        }

    Returns:
        {
            "event_id": str,
            "html_link": str,
            "message": str
        }
    """
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    # Validate required fields
    if 'summary' not in event_data or 'start_time' not in event_data:
        raise HTTPException(status_code=400, detail="summary and start_time are required")

    try:
        # Parse times
        start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))

        # Default end time: start + 1 hour
        if 'end_time' in event_data:
            end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
        else:
            end_time = start_time + timedelta(hours=1)

        # Build event
        event = {
            'summary': event_data['summary'],
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        if 'location' in event_data and event_data['location']:
            event['location'] = event_data['location']

        if 'description' in event_data and event_data['description']:
            event['description'] = event_data['description']

        # Create event
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


@router.post("/events/create-from-detected/{event_id}")
def create_event_from_detected(event_id: int):
    """
    Create Google Calendar event from a detected email event.

    Args:
        event_id: ID of the detected event (from detected_events table)

    Returns:
        {
            "calendar_event_id": str,
            "google_event_id": str,
            "html_link": str,
            "message": str
        }
    """
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /calendar/auth")

    # Get detected event
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT title, date_time, location, url, attendees, approval_status
                FROM detected_events
                WHERE id = :event_id
            """),
            {"event_id": event_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Detected event {event_id} not found")

        title, date_time, location, url, attendees, approval_status = row

        if approval_status != 'approved':
            raise HTTPException(status_code=400, detail="Event must be approved first. Use POST /emails/events/{id}/approve")

    # Prepare event data
    event_data = {
        "summary": title,
        "start_time": date_time
    }

    if location:
        event_data["location"] = location

    # Add URL to description
    description_parts = []
    if url:
        description_parts.append(f"Link: {url}")
    if attendees:
        description_parts.append(f"Attendees: {attendees}")
    if description_parts:
        event_data["description"] = "\n".join(description_parts)

    # Create calendar event
    try:
        result = create_event(event_data)

        # Store in calendar_events table
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO calendar_events (
                        google_event_id, title, start_time, end_time,
                        location, url, source, detected_event_id
                    ) VALUES (
                        :google_id, :title, :start_time, :end_time,
                        :location, :url, 'detected_email', :detected_id
                    )
                """),
                {
                    "google_id": result["event_id"],
                    "title": title,
                    "start_time": date_time,
                    "end_time": None,  # TODO: Calculate end time
                    "location": location,
                    "url": url,
                    "detected_id": event_id
                }
            )

        print(f"✅ Created calendar event from detected event #{event_id}")

        return {
            "calendar_event_id": result["event_id"],
            "google_event_id": result["event_id"],
            "html_link": result.get("html_link"),
            "message": f"Event added to Google Calendar: {title}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating calendar event: {str(e)}")


@router.get("/conflicts")
def check_conflicts(start_time: str, end_time: str, calendar_id: str = "primary"):
    """
    Check for conflicts in calendar for a given time range.

    Query params:
        start_time: ISO format datetime
        end_time: ISO format datetime
        calendar_id: Calendar ID (default: "primary")

    Returns:
        {
            "has_conflict": bool,
            "conflicting_events": [...]
        }
    """
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

        return {
            "has_conflict": len(conflicting_events) > 0,
            "conflicting_events": conflicting_events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking conflicts: {str(e)}")
