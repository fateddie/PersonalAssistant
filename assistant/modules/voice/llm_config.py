"""
LLM Configuration
=================
OpenAI client configuration and initialization.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables (check .env.local first, then .env)
project_root = Path(__file__).parent.parent.parent.parent
env_local = project_root / ".env.local"
env_file = project_root / ".env"

if env_local.exists():
    load_dotenv(env_local)
load_dotenv(env_file)  # Load .env as fallback for missing vars

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize OpenAI client
client = None
if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your-"):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"OpenAI client initialization failed: {e}")


def is_configured() -> bool:
    """Check if OpenAI is properly configured"""
    return client is not None
