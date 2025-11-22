"""
Calendar Configuration
======================
Configuration and constants for Google Calendar integration.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
config_dir = Path(__file__).parent.parent.parent.parent / "config" / ".env"
load_dotenv(config_dir)

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

# Alias for backward compatibility
CALENDAR_ENABLED = GOOGLE_CALENDAR_ENABLED
