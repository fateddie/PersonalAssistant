"""
Calendar Service
================
Google Calendar service initialization and management.
"""

import json
from typing import Optional

from .calendar_config import (
    GOOGLE_CALENDAR_ENABLED,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    TOKEN_FILE,
)

# Google Calendar API client (initialized on first use)
calendar_service = None


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
            with open(TOKEN_FILE, "r") as token:
                creds_data = json.load(token)
                creds = Credentials.from_authorized_user_info(creds_data)

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        if creds and creds.valid:
            calendar_service = build("calendar", "v3", credentials=creds)
            print("✅ Google Calendar service initialized")
            return calendar_service

        # Need to authenticate
        print("⚠️  Google Calendar authentication required. Visit /calendar/auth")
        return None

    except ImportError:
        print(
            "⚠️  google-api-python-client not installed. Install with: pip install google-auth google-auth-oauthlib google-api-python-client"
        )
        return None
    except Exception as e:
        print(f"❌ Error initializing Google Calendar: {e}")
        return None
