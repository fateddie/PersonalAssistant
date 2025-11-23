"""
Prompt Coach Module
===================
Transforms messy brain-dumps into well-structured prompts through
coaching, interrogation, and critique.

Components:
- coach.py: Main coaching logic and session management
- extractor.py: Parse brain-dump into template sections
- interrogator.py: Generate clarifying questions
- critic.py: Critique and teach prompt engineering
- system_prompts.py: AI prompts for each stage
"""

from typing import Callable

# Module will be registered with the orchestrator
__all__ = ["register"]


def register(app, publish: Callable, subscribe: Callable):
    """
    Register module with orchestrator.

    Args:
        app: FastAPI application instance
        publish: Function to publish events
        subscribe: Function to subscribe to events
    """
    from .coach import router as coach_router

    # Register API routes
    app.include_router(coach_router, prefix="/prompt-coach", tags=["prompt-coach"])

    # Subscribe to relevant events (if any)
    # subscribe("user.session.started", on_session_started)

    print("✅ Prompt Coach module registered")
