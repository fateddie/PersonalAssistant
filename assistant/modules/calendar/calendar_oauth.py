"""
Calendar OAuth
==============
OAuth2 authentication endpoints for Google Calendar.
"""

import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from .calendar_config import (
    GOOGLE_CALENDAR_ENABLED,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    TOKEN_FILE,
)

router = APIRouter()


@router.get("/auth")
def start_oauth_flow():
    """
    Start OAuth2 authentication flow.
    Redirects user to Google consent screen.
    """
    if not GOOGLE_CALENDAR_ENABLED:
        return {
            "error": "Google Calendar integration is disabled. Set GOOGLE_CALENDAR_ENABLED=true in config/.env"
        }

    try:
        from google_auth_oauthlib.flow import Flow

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
            scopes=["https://www.googleapis.com/auth/calendar"],
        )

        flow.redirect_uri = GOOGLE_REDIRECT_URI

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )

        return RedirectResponse(url=authorization_url)

    except ImportError:
        raise HTTPException(status_code=500, detail="google-auth-oauthlib not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth flow error: {str(e)}")


@router.get("/oauth/callback")
def oauth_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """
    OAuth2 callback endpoint.
    Google redirects here after user grants permission.
    """
    if error:
        return {
            "status": "error",
            "error": error,
            "message": f"Authentication failed: {error}. User may have denied access or there was a configuration error.",
        }

    if not code:
        return {
            "status": "error",
            "message": "No authorization code received from Google. Please try again.",
            "help": "Visit /calendar/auth to start the authentication process",
        }

    try:
        from google_auth_oauthlib.flow import Flow

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
            scopes=["https://www.googleapis.com/auth/calendar"],
            state=state,
        )

        flow.redirect_uri = GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)

        creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

        print("✅ Google Calendar authentication successful")

        return {
            "status": "success",
            "message": "Google Calendar connected! You can now create events.",
            "expires_at": creds.expiry.isoformat() if creds.expiry else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/status")
def get_calendar_status():
    """Get Google Calendar connection status."""
    authenticated = False
    token_expires = None

    if GOOGLE_CALENDAR_ENABLED and TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r") as token:
                creds_data = json.load(token)
                authenticated = True
                token_expires = creds_data.get("expiry")
        except (json.JSONDecodeError, IOError):
            pass

    return {
        "enabled": GOOGLE_CALENDAR_ENABLED,
        "authenticated": authenticated,
        "token_expires": token_expires,
        "setup_url": "/calendar/auth" if not authenticated else None,
    }
