"""
Prompt Coach - Main Coaching Logic
==================================
FastAPI router and session management for the coaching flow.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import uuid
from datetime import datetime

from .models import (
    CoachSession,
    SessionState,
    StartSessionRequest,
    StartSessionResponse,
    AnswerQuestionsRequest,
    AnswerQuestionsResponse,
    CompleteSessionResponse,
)
from .extractor import extract_template
from .interrogator import generate_questions
from .critic import generate_critique

router = APIRouter()

# In-memory session storage (for MVP - can add DB persistence later)
_sessions: Dict[str, CoachSession] = {}


def _get_session(session_id: str) -> CoachSession:
    """Get session by ID or raise 404"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return _sessions[session_id]


@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest) -> StartSessionResponse:
    """
    Start a new coaching session with a brain-dump prompt.

    This will:
    1. Create a new session
    2. Extract what we can into the template
    3. Generate clarifying questions for gaps
    """
    # Create new session
    session_id = str(uuid.uuid4())[:8]
    session = CoachSession(
        session_id=session_id,
        original_prompt=request.brain_dump,
        created_at=datetime.now().isoformat(),
    )

    # Extract template from brain-dump
    session.template = extract_template(request.brain_dump)
    session.state = SessionState.EXTRACT

    # Generate clarifying questions for missing/unclear sections
    session.questions = generate_questions(session.template)

    if session.questions:
        session.state = SessionState.INTERROGATE
        message = f"I've extracted what I can. I have {len(session.questions)} questions to fill in the gaps."
    else:
        session.state = SessionState.CRITIQUE
        message = "Your prompt is fairly complete! Let me generate a critique and improvements."

    # Store session
    _sessions[session_id] = session

    return StartSessionResponse(
        session_id=session_id,
        state=session.state,
        template=session.template,
        questions=session.questions,
        message=message,
    )


@router.post("/answer", response_model=AnswerQuestionsResponse)
async def answer_questions(request: AnswerQuestionsRequest) -> AnswerQuestionsResponse:
    """
    Process user's answers to clarifying questions.

    This will:
    1. Update the template with new information
    2. Check if more questions are needed
    3. Move to critique stage if complete
    """
    session = _get_session(request.session_id)

    # Store answers
    session.answers.update(request.answers)

    # Re-extract/fill template with new context
    combined_context = session.original_prompt + "\n\nAdditional context:\n"
    for q_id, answer in request.answers.items():
        # Find the question text
        for q in session.questions:
            if q.id == q_id:
                combined_context += f"Q: {q.question}\nA: {answer}\n\n"
                break

    # Re-extract with enriched context
    session.template = extract_template(combined_context)

    # Check if we need more questions
    session.questions = generate_questions(session.template)

    if session.questions:
        session.state = SessionState.INTERROGATE
        message = f"Thanks! I still have {len(session.questions)} more questions."
    else:
        session.state = SessionState.CRITIQUE
        message = "Great! I have everything I need. Generating your improved prompt..."

    # Update stored session
    _sessions[request.session_id] = session

    return AnswerQuestionsResponse(
        session_id=request.session_id,
        state=session.state,
        template=session.template,
        questions=session.questions,
        message=message,
    )


@router.get("/complete/{session_id}", response_model=CompleteSessionResponse)
async def complete_session(session_id: str) -> CompleteSessionResponse:
    """
    Complete the session and get final prompt with critique.

    This will:
    1. Generate the final structured prompt
    2. Create critique comparing original vs improved
    3. Extract lessons learned
    """
    session = _get_session(session_id)

    # Generate critique and lessons
    session.critique = generate_critique(session.original_prompt, session.template)

    # Build final prompt from template
    session.final_prompt = _build_final_prompt(session.template)
    session.state = SessionState.COMPLETE

    # Update stored session
    _sessions[session_id] = session

    return CompleteSessionResponse(
        session_id=session_id,
        original_prompt=session.original_prompt,
        final_prompt=session.final_prompt,
        template=session.template,
        critique=session.critique,
        message="Here's your improved prompt with lessons learned!",
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> CoachSession:
    """Get current session state"""
    return _get_session(session_id)


def _build_final_prompt(template) -> str:
    """Build the final prompt string from template sections"""
    sections = []

    if template.context.content:
        sections.append(f"## CONTEXT\n{template.context.content}")

    if template.constraints.content:
        sections.append(f"## CONSTRAINTS\n{template.constraints.content}")

    if template.inputs.content:
        sections.append(f"## INPUTS\n{template.inputs.content}")

    if template.task.content:
        sections.append(f"## TASK\n{template.task.content}")

    if template.evaluation.content:
        sections.append(f"## EVALUATION\n{template.evaluation.content}")

    if template.output_format.content:
        sections.append(f"## OUTPUT FORMAT\n{template.output_format.content}")

    return "\n\n".join(sections)
