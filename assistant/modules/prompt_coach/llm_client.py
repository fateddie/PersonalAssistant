"""
LLM Client for Prompt Coach
===========================
Shared OpenAI client configuration for the prompt coach module.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Any

# Load environment variables
project_root = Path(__file__).parent.parent.parent.parent
env_local = project_root / ".env.local"
env_file = project_root / ".env"

if env_local.exists():
    load_dotenv(env_local)
load_dotenv(env_file)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Use gpt-4o-mini for cost efficiency; can upgrade to gpt-4o for better quality
OPENAI_MODEL = os.getenv("PROMPT_COACH_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

# Initialize client
_client: Optional[OpenAI] = None
if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your-"):
    try:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"❌ Prompt Coach: OpenAI client init failed: {e}")


def is_configured() -> bool:
    """Check if OpenAI is properly configured"""
    return _client is not None


def call_llm(system_prompt: str, user_message: str, expect_json: bool = True) -> Dict[str, Any]:
    """
    Call OpenAI API with the given prompts.

    Args:
        system_prompt: The system prompt defining the AI's role
        user_message: The user's input to process
        expect_json: If True, parse response as JSON

    Returns:
        Parsed JSON dict if expect_json=True, else {"text": response_text}
    """
    if not _client:
        return {"error": "OpenAI not configured. Set OPENAI_API_KEY in .env"}

    try:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            response_format={"type": "json_object"} if expect_json else None,
        )

        content = response.choices[0].message.content or ""

        if expect_json:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": f"Failed to parse JSON response: {content[:200]}"}
        else:
            return {"text": content}

    except Exception as e:
        return {"error": f"LLM call failed: {str(e)}"}
