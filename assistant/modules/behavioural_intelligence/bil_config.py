"""
BIL Configuration
=================
Database engine and feature flags for behavioral intelligence.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine

# Database connection
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///assistant/data/memory.db")
engine = create_engine(DB_PATH.replace("sqlite:///", "sqlite:///"))

# Import Supabase memory for ManagementTeam project integration
try:
    from assistant.core.supabase_memory import (
        _get_supabase_client,
        get_tasks_for_project,
        DEPENDENCIES_AVAILABLE,
    )

    SUPABASE_AVAILABLE = DEPENDENCIES_AVAILABLE
except ImportError:
    SUPABASE_AVAILABLE = False
    _get_supabase_client = None
    get_tasks_for_project = None
    print(
        "⚠️  Supabase memory not available - ManagementTeam projects won't be shown in morning check-in"
    )

# Import progress report functions for daily summaries
try:
    # Add scripts directory to path
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.progress_report import get_managementteam_activity, get_asksharon_activity

    PROGRESS_REPORTS_AVAILABLE = True
except ImportError:
    PROGRESS_REPORTS_AVAILABLE = False
    get_managementteam_activity = None
    get_asksharon_activity = None
