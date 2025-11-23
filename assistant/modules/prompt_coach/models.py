"""
Prompt Coach Models
===================
Pydantic models for request/response and internal state.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum


class SessionState(str, Enum):
    """States in the coaching state machine"""

    START = "start"
    EXTRACT = "extract"
    INTERROGATE = "interrogate"
    WAITING = "waiting"
    FILL = "fill"
    CRITIQUE = "critique"
    OUTPUT = "output"
    COMPLETE = "complete"


class SectionStatus(str, Enum):
    """Status of a template section"""

    FILLED = "filled"
    MISSING = "missing"
    UNCLEAR = "unclear"


class TemplateSection(BaseModel):
    """A single section of the prompt template"""

    content: str = ""
    status: SectionStatus = SectionStatus.MISSING
    notes: Optional[str] = None  # Why it's unclear, suggestions, etc.


class PromptTemplate(BaseModel):
    """The 6-section structured prompt template"""

    context: TemplateSection = TemplateSection()
    constraints: TemplateSection = TemplateSection()
    inputs: TemplateSection = TemplateSection()
    task: TemplateSection = TemplateSection()
    evaluation: TemplateSection = TemplateSection()
    output_format: TemplateSection = TemplateSection()

    def get_missing_sections(self) -> List[str]:
        """Return list of section names that are missing or unclear"""
        missing = []
        for name in ["context", "constraints", "inputs", "task", "evaluation", "output_format"]:
            section = getattr(self, name)
            if section.status in [SectionStatus.MISSING, SectionStatus.UNCLEAR]:
                missing.append(name)
        return missing

    def is_complete(self) -> bool:
        """Check if all sections are filled"""
        return len(self.get_missing_sections()) == 0


class ClarifyingQuestion(BaseModel):
    """A question to ask the user"""

    id: str  # e.g., "q1", "q2"
    section: str  # Which template section this addresses
    question: str
    priority: int = 1  # 1 = critical, 2 = important, 3 = nice-to-have


class Lesson(BaseModel):
    """A prompt engineering lesson learned"""

    title: str
    explanation: str
    example_before: Optional[str] = None
    example_after: Optional[str] = None


class Critique(BaseModel):
    """Critique of the original prompt"""

    overall_score: int  # 1-10
    strengths: List[str]
    weaknesses: List[str]
    lessons: List[Lesson]


class CoachSession(BaseModel):
    """Full coaching session state"""

    session_id: str
    state: SessionState = SessionState.START
    original_prompt: str = ""
    template: PromptTemplate = PromptTemplate()
    questions: List[ClarifyingQuestion] = []
    answers: Dict[str, str] = {}  # question_id -> answer
    critique: Optional[Critique] = None
    final_prompt: str = ""
    created_at: Optional[str] = None


# API Request/Response Models


class StartSessionRequest(BaseModel):
    """Request to start a new coaching session"""

    brain_dump: str


class StartSessionResponse(BaseModel):
    """Response after starting session"""

    session_id: str
    state: SessionState
    template: PromptTemplate
    questions: List[ClarifyingQuestion]
    message: str


class AnswerQuestionsRequest(BaseModel):
    """Request with answers to clarifying questions"""

    session_id: str
    answers: Dict[str, str]  # question_id -> answer


class AnswerQuestionsResponse(BaseModel):
    """Response after processing answers"""

    session_id: str
    state: SessionState
    template: PromptTemplate
    questions: List[ClarifyingQuestion]  # May have follow-up questions
    message: str


class CompleteSessionResponse(BaseModel):
    """Final response with complete prompt and lessons"""

    session_id: str
    original_prompt: str
    final_prompt: str
    template: PromptTemplate
    critique: Critique
    message: str
